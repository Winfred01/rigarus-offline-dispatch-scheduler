$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'TauriSqliteSnapshot.ps1')
if (-not ('RigarusSqliteFixture' -as [type])) {
    Add-Type -TypeDefinition @'
using System;using System.IO;using System.Text;using System.Threading;using System.Runtime.InteropServices;
[assembly: DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
public sealed class RigarusSqliteFixture:IDisposable {
 [DllImport("winsqlite3.dll",CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_open_v2(byte[] p,out IntPtr db,int flags,IntPtr vfs);
 [DllImport("winsqlite3.dll",CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_exec(IntPtr db,byte[] sql,IntPtr callback,IntPtr state,out IntPtr error);
 [DllImport("winsqlite3.dll",CallingConvention=CallingConvention.Cdecl)] static extern void sqlite3_free(IntPtr p);
 [DllImport("winsqlite3.dll",CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_close_v2(IntPtr db);
 [DllImport("winsqlite3.dll",CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_busy_timeout(IntPtr db,int ms);
 IntPtr db;Thread thread;volatile bool stop;public int Commits;public Exception BackgroundError;
 static byte[] Utf8(string s){return Encoding.UTF8.GetBytes(s+"\0");}
 public RigarusSqliteFixture(string path){int rc=sqlite3_open_v2(Utf8(path),out db,2|4,IntPtr.Zero);if(rc!=0)throw new IOException("Synthetic fixture open failed: "+rc);sqlite3_busy_timeout(db,1000);}
 public void Exec(string sql){IntPtr error;int rc=sqlite3_exec(db,Utf8(sql),IntPtr.Zero,IntPtr.Zero,out error);if(error!=IntPtr.Zero)sqlite3_free(error);if(rc!=0)throw new IOException("Synthetic fixture SQL failed: "+rc);}
 public void StartFlipping(){thread=new Thread(()=>{try{while(!stop){int v=Commits%2;Exec("BEGIN IMMEDIATE; UPDATE A SET V="+v+"; UPDATE B SET V="+v+"; COMMIT;");Interlocked.Increment(ref Commits);Thread.Sleep(1);}}catch(Exception e){BackgroundError=e;}});thread.IsBackground=true;thread.Start();}
 public void StopFlipping(){stop=true;if(thread!=null && !thread.Join(5000))throw new TimeoutException("Synthetic fixture writer did not stop.");if(BackgroundError!=null)throw BackgroundError;}
 public void Dispose(){StopFlipping();if(db!=IntPtr.Zero){int rc=sqlite3_close_v2(db);db=IntPtr.Zero;if(rc!=0)throw new IOException("Synthetic fixture close failed: "+rc);}}
}
'@
}
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('rigarus-sqlite-harness-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $testRoot | Out-Null
$writer = $null; $concurrent = $null; $exclusive = $null
function Snapshot([string]$Path) { Get-AcceptanceSqliteSnapshot -Path $Path -TimeoutSeconds 5 }
function Assert-ReadFails([string]$Path, [int]$Timeout = 5) {
    $failed = $false
    try { Get-AcceptanceSqliteSnapshot -Path $Path -TimeoutSeconds $Timeout | Out-Null }
    catch { $failed = $true }
    if (-not $failed) { throw 'Unreadable/corrupt/locked synthetic database produced a fingerprint.' }
}
try {
    $db = Join-Path $testRoot 'fixture with spaces.db'
    $writer = [RigarusSqliteFixture]::new($db)
    $writer.Exec("PRAGMA journal_mode=WAL; CREATE TABLE Records(Id INTEGER PRIMARY KEY, Value, Note TEXT); INSERT INTO Records VALUES(1,1,'Synthetic retained note'); CREATE TABLE Audit(Id INTEGER PRIMARY KEY AUTOINCREMENT, Note); INSERT INTO Audit(Note) VALUES('Synthetic event'); CREATE TABLE Pairs(K TEXT PRIMARY KEY, V BLOB) WITHOUT ROWID; INSERT INTO Pairs VALUES('b',x'00FF'),('a',x''); CREATE TABLE Duplicates(V); INSERT INTO Duplicates VALUES(NULL),(NULL); CREATE TABLE ""Quoted""""Table""(V); INSERT INTO ""Quoted""""Table"" VALUES('Synthetic quote');")
    $baseline = Snapshot $db
    if ($baseline.Tables -ne 6 -or $baseline.Rows -ne 8 -or $baseline.Digest.Length -ne 64) { throw 'Snapshot omitted a table, sequence or duplicate row.' }
    if ($baseline.Digest -cne (Snapshot $db).Digest) { throw 'An unchanged active WAL database changed logical digest.' }
    $oldSharingFailure = $false
    try { Get-FileHash -LiteralPath ($db + '-wal') | Out-Null }
    catch { $oldSharingFailure = $true }
    $writer.Exec('PRAGMA wal_checkpoint(TRUNCATE);')
    if ($baseline.Digest -cne (Snapshot $db).Digest) { throw 'WAL checkpoint caused a false business mutation.' }
    $writer.Dispose(); $writer = $null
    if ($baseline.Digest -cne (Snapshot $db).Digest) { throw 'Last-connection WAL cleanup caused a false mutation.' }
    $writer = [RigarusSqliteFixture]::new($db)
    foreach ($change in @(
        @{ Sql = "UPDATE Records SET Note='Synthetic changed note' WHERE Id=1"; Undo = "UPDATE Records SET Note='Synthetic retained note' WHERE Id=1" },
        @{ Sql = "INSERT INTO Records VALUES(2,2,'Synthetic added row')"; Undo = 'DELETE FROM Records WHERE Id=2' },
        @{ Sql = 'DELETE FROM Records WHERE Id=1'; Undo = "INSERT INTO Records VALUES(1,1,'Synthetic retained note')" },
        @{ Sql = 'UPDATE Records SET Value=NULL'; Undo = 'UPDATE Records SET Value=1' },
        @{ Sql = "UPDATE Records SET Value='1'"; Undo = 'UPDATE Records SET Value=1' },
        @{ Sql = 'UPDATE Records SET Value=1.0'; Undo = 'UPDATE Records SET Value=1' },
        @{ Sql = "UPDATE Records SET Value=x'31'"; Undo = 'UPDATE Records SET Value=1' },
        @{ Sql = "UPDATE Records SET Value=''"; Undo = 'UPDATE Records SET Value=1' },
        @{ Sql = 'DELETE FROM Duplicates WHERE rowid=1'; Undo = 'INSERT INTO Duplicates VALUES(NULL)' },
        @{ Sql = 'CREATE TABLE Added(V)'; Undo = 'DROP TABLE Added' }
    )) {
        $writer.Exec($change.Sql)
        if ($baseline.Digest -ceq (Snapshot $db).Digest) { throw ('Real logical mutation escaped: ' + $change.Sql) }
        $writer.Exec($change.Undo)
        if ($baseline.Digest -cne (Snapshot $db).Digest) { throw 'Equivalent records did not regain the canonical fingerprint.' }
    }
    $writer.Exec("INSERT INTO Audit(Note) VALUES('Synthetic next ID');DELETE FROM Audit WHERE Id=2;")
    if ($baseline.Digest -ceq (Snapshot $db).Digest) { throw 'Changed ID sequence escaped verification.' }
    $writer.Exec("UPDATE sqlite_sequence SET seq=1 WHERE name='Audit'")
    $typed = @()
    foreach ($literal in @('NULL', "''", '1', '1.0', "'1'", "x'31'")) {
        $writer.Exec('UPDATE Records SET Value=' + $literal)
        $typed += (Snapshot $db).Digest
    }
    if (@($typed | Sort-Object -Unique).Count -ne 6) { throw 'Null, empty, integer, real, text and BLOB values collided.' }
    $writer.Exec("UPDATE Records SET Value=1, Note=CAST(x'E4B8AD00F09F9880' AS TEXT)")
    $nulText = (Snapshot $db).Digest
    $writer.Exec("UPDATE Records SET Note=CAST(x'E4B8AD00F09F9881' AS TEXT)")
    if ($nulText -ceq (Snapshot $db).Digest) { throw 'Unicode text after an embedded NUL escaped verification.' }
    $writer.Exec("UPDATE Records SET Note='Synthetic retained note'")
    $writer.Exec('VACUUM;')
    if ($baseline.Digest -cne (Snapshot $db).Digest) { throw 'Physical layout maintenance changed logical rows.' }
    $writer.Dispose(); $writer = $null
    Assert-ReadFails (Join-Path $testRoot 'missing.db')
    $corrupt = Join-Path $testRoot 'corrupt.db'; [IO.File]::WriteAllText($corrupt, 'Synthetic not-a-database')
    Assert-ReadFails $corrupt
    $fkDb = Join-Path $testRoot 'invalid-fk.db'
    $fkWriter = [RigarusSqliteFixture]::new($fkDb)
    try {
        $fkWriter.Exec('CREATE TABLE Parent(Id INTEGER PRIMARY KEY);CREATE TABLE Child(P INTEGER REFERENCES Parent(Id));INSERT INTO Child VALUES(99);')
        Assert-ReadFails $fkDb
    }
    finally { $fkWriter.Dispose() }
    $locked = [IO.File]::Open($db, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    try { Assert-ReadFails $db } finally { $locked.Dispose() }

    $busyDb = Join-Path $testRoot 'busy.db'; $exclusive = [RigarusSqliteFixture]::new($busyDb)
    $exclusive.Exec('PRAGMA journal_mode=DELETE;CREATE TABLE Fixture(V);INSERT INTO Fixture VALUES(1);BEGIN EXCLUSIVE;')
    $bound = [Diagnostics.Stopwatch]::StartNew(); $timedOut = $false
    try { Get-AcceptanceSqliteSnapshot -Path $busyDb -TimeoutSeconds 1 | Out-Null }
    catch {
        $errorNode = $_.Exception
        while ($errorNode) { if ($errorNode.Data['AcceptanceStatus'] -eq 'TIMEOUT') { $timedOut = $true }; $errorNode = $errorNode.InnerException }
    }
    if (-not $timedOut -or $bound.Elapsed.TotalSeconds -gt 5) { throw 'Exclusive-lock timeout was missing, unbounded or silently passed.' }
    $exclusive.Exec('ROLLBACK'); $exclusive.Dispose(); $exclusive = $null

    $concurrentDb = Join-Path $testRoot 'concurrent.db'; $concurrent = [RigarusSqliteFixture]::new($concurrentDb)
    $concurrent.Exec('PRAGMA journal_mode=WAL;CREATE TABLE A(V);CREATE TABLE B(V);INSERT INTO A VALUES(0);INSERT INTO B VALUES(0);')
    $zero = (Snapshot $concurrentDb).Digest
    $concurrent.Exec('BEGIN IMMEDIATE;UPDATE A SET V=1;UPDATE B SET V=1;COMMIT;')
    $one = (Snapshot $concurrentDb).Digest
    $concurrent.StartFlipping()
    foreach ($iteration in 1..100) {
        $observed = (Snapshot $concurrentDb).Digest
        if ($observed -cne $zero -and $observed -cne $one) { throw 'Snapshot mixed records from different committed transactions.' }
    }
    $concurrent.StopFlipping()
    if ($concurrent.Commits -lt 1) { throw 'Concurrent writer never committed; consistency test was ineffective.' }
    Write-Host ('PASS: active WAL/checkpoint/cleanup; original hash sharing failure=' + $oldSharingFailure + '; SQLite=' + $baseline.SqliteVersion)
    Write-Host ('PASS: real insert/update/delete/type/schema/sequence changes, canonical duplicates, WITHOUT ROWID and quoted identifiers; concurrent commits=' + $concurrent.Commits)
    Write-Host 'PASS: missing/corrupt/exclusively locked reads fail; bounded lock timeout; 100 consistent multi-table snapshots.'
}
finally {
    foreach ($connection in @($writer, $concurrent, $exclusive)) { if ($connection) { $connection.Dispose() } }
    $resolved = [IO.Path]::GetFullPath($testRoot)
    if ((Split-Path -Parent $resolved) -ne [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') -or
        (Split-Path -Leaf $resolved) -notmatch '^rigarus-sqlite-harness-[0-9a-f]{32}$') { throw 'Unsafe synthetic cleanup path.' }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
