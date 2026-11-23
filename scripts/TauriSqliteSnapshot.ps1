# Acceptance-only reader. Uses the Windows system SQLite; never ships in the app.
if (-not ('RigarusAcceptanceSqlite.Snapshot' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
[assembly: DefaultDllImportSearchPaths(DllImportSearchPath.System32)]
namespace RigarusAcceptanceSqlite {
 public sealed class Fingerprint {
  public string Digest; public string SqliteVersion; public int Tables; public long Rows; public long ElapsedMs;
 }
 public static class Snapshot {
  const string Dll="winsqlite3.dll";
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_open_v2(byte[] path,out IntPtr db,int flags,IntPtr vfs);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_close_v2(IntPtr db);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_db_readonly(IntPtr db,byte[] name);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_busy_timeout(IntPtr db,int ms);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern IntPtr sqlite3_libversion();
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_prepare_v2(IntPtr db,byte[] sql,int count,out IntPtr stmt,IntPtr tail);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_step(IntPtr stmt);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_finalize(IntPtr stmt);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_column_count(IntPtr stmt);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_column_type(IntPtr stmt,int column);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern long sqlite3_column_int64(IntPtr stmt,int column);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern double sqlite3_column_double(IntPtr stmt,int column);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern IntPtr sqlite3_column_text(IntPtr stmt,int column);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern IntPtr sqlite3_column_blob(IntPtr stmt,int column);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern int sqlite3_column_bytes(IntPtr stmt,int column);
  [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate int Progress(IntPtr state);
  [DllImport(Dll,CallingConvention=CallingConvention.Cdecl)] static extern void sqlite3_progress_handler(IntPtr db,int operations,Progress callback,IntPtr state);
  static byte[] Utf8(string text){return Encoding.UTF8.GetBytes(text+"\0");}
  sealed class Budget {
   public readonly Stopwatch Clock=Stopwatch.StartNew(); public readonly int Seconds; public long Bytes,Rows;
   public Budget(int seconds){Seconds=seconds;}
   public bool Expired {get{return Clock.Elapsed.TotalSeconds>=Seconds;}}
   public void Check(){if(Expired){var e=new TimeoutException("Synthetic SQLite snapshot deadline exceeded.");e.Data["AcceptanceStatus"]="TIMEOUT";throw e;}}
   public void Add(long bytes){Check();Bytes+=bytes;if(Bytes>128L*1024*1024)throw new InvalidOperationException("Synthetic SQLite snapshot exceeds 128 MiB; no partial fingerprint returned.");}
  }
  static void Check(int rc,string phase,Budget budget){budget.Check();if(rc!=0)throw new IOException("Synthetic SQLite snapshot failed: phase="+phase+" sqliteCode="+rc+"; no fingerprint returned.");}
  static void Query(IntPtr db,string sql,Budget budget,Action<IntPtr> row){
   IntPtr stmt=IntPtr.Zero;budget.Check();
   try {
    Check(sqlite3_prepare_v2(db,Utf8(sql),-1,out stmt,IntPtr.Zero),"prepare",budget);
    while(true){budget.Check();int rc=sqlite3_step(stmt);if(rc==101)break;if(rc!=100){Check(rc,"step",budget);break;}row(stmt);}
   } finally {if(stmt!=IntPtr.Zero)sqlite3_finalize(stmt);}
  }
  static byte[] ValueBytes(IntPtr stmt,int col,bool blob,Budget budget){
   IntPtr ptr=blob?sqlite3_column_blob(stmt,col):sqlite3_column_text(stmt,col);
   int length=sqlite3_column_bytes(stmt,col);budget.Add(length);
   if(length<0 || (!blob && ptr==IntPtr.Zero) || (length>0 && ptr==IntPtr.Zero))throw new IOException("Synthetic SQLite value could not be read.");
   var bytes=new byte[length];if(length>0)Marshal.Copy(ptr,bytes,0,length);return bytes;
  }
  static string Text(IntPtr stmt,int col,Budget budget){return new UTF8Encoding(false,true).GetString(ValueBytes(stmt,col,false,budget));}
  static byte[] Row(IntPtr stmt,Budget budget){
   if(++budget.Rows>1000000)throw new InvalidOperationException("Synthetic SQLite snapshot exceeds one million rows; no partial fingerprint returned.");
   using(var stream=new MemoryStream())using(var writer=new BinaryWriter(stream)){
    int columns=sqlite3_column_count(stmt);writer.Write(columns);
    for(int i=0;i<columns;i++){
     int type=sqlite3_column_type(stmt,i);writer.Write((byte)type);
     switch(type){
      case 1:writer.Write(sqlite3_column_int64(stmt,i));break;
      case 2:writer.Write(BitConverter.DoubleToInt64Bits(sqlite3_column_double(stmt,i)));break;
      case 3:case 4:var bytes=ValueBytes(stmt,i,type==4,budget);writer.Write(bytes.Length);writer.Write(bytes);break;
      case 5:break;
      default:throw new IOException("Synthetic SQLite value has an unknown storage type.");
     }
    }
    writer.Flush();budget.Add(stream.Length);return stream.ToArray();
   }
  }
  sealed class ByteOrder:IComparer<byte[]> {
   readonly Budget budget;public ByteOrder(Budget value){budget=value;}
   public int Compare(byte[] a,byte[] b){budget.Check();int count=Math.Min(a.Length,b.Length);for(int i=0;i<count;i++){int c=a[i].CompareTo(b[i]);if(c!=0)return c;}return a.Length.CompareTo(b.Length);}
  }
  static void WriteRows(BinaryWriter writer,List<byte[]> rows,Budget budget){rows.Sort(new ByteOrder(budget));writer.Write(rows.Count);foreach(var row in rows){budget.Check();writer.Write(row.Length);writer.Write(row);}}
  public static Fingerprint Read(string path,int timeoutSeconds){
   if(timeoutSeconds<1 || timeoutSeconds>300)throw new ArgumentOutOfRangeException("timeoutSeconds");
   if(!Path.IsPathRooted(path) || !File.Exists(path))throw new FileNotFoundException("Synthetic SQLite database is missing or inaccessible; no fingerprint returned.");
   var budget=new Budget(timeoutSeconds);IntPtr db=IntPtr.Zero;Exception failure=null;
   Progress progress=delegate(IntPtr state){return budget.Expired?1:0;};
   try {
    // READONLY + PRIVATECACHE. No URI/immutable/nolock flag, no CREATE, no write connection.
    Check(sqlite3_open_v2(Utf8(path),out db,1|0x40000,IntPtr.Zero),"open-readonly",budget);
    if(sqlite3_db_readonly(db,Utf8("main"))!=1)throw new IOException("Synthetic snapshot connection is not read-only.");
    Check(sqlite3_busy_timeout(db,Math.Min(timeoutSeconds*1000,5000)),"busy-timeout",budget);
    sqlite3_progress_handler(db,1000,progress,IntPtr.Zero);
    Query(db,"PRAGMA query_only=ON",budget,delegate(IntPtr s){});
    Query(db,"BEGIN",budget,delegate(IntPtr s){});
    var names=new List<string>();var schema=new List<byte[]>();
    // First SELECT pins the same read transaction used for every subsequent table/check.
    Query(db,"SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' OR name='sqlite_sequence' ORDER BY type,name COLLATE BINARY",budget,delegate(IntPtr s){schema.Add(Row(s,budget));});
    Query(db,"SELECT name FROM sqlite_schema WHERE type='table' AND (name NOT LIKE 'sqlite_%' OR name='sqlite_sequence') ORDER BY name COLLATE BINARY",budget,delegate(IntPtr s){if(names.Count>=256)throw new InvalidOperationException("Synthetic SQLite snapshot exceeds 256 tables.");names.Add(Text(s,0,budget));});
    Query(db,"PRAGMA integrity_check",budget,delegate(IntPtr s){if(Text(s,0,budget)!="ok")throw new IOException("Synthetic SQLite integrity check failed.");});
    Query(db,"PRAGMA foreign_key_check",budget,delegate(IntPtr s){throw new IOException("Synthetic SQLite foreign-key check failed.");});
    using(var content=new MemoryStream())using(var writer=new BinaryWriter(content,Encoding.UTF8)){
     writer.Write("Rigarus logical SQLite snapshot v1");WriteRows(writer,schema,budget);
     Query(db,"PRAGMA user_version",budget,delegate(IntPtr s){writer.Write(sqlite3_column_int64(s,0));});
     Query(db,"PRAGMA application_id",budget,delegate(IntPtr s){writer.Write(sqlite3_column_int64(s,0));});
     writer.Write(names.Count);long records=0;
     foreach(string name in names){
      budget.Check();writer.Write(name);var rows=new List<byte[]>();
      Query(db,"SELECT * FROM \""+name.Replace("\"","\"\"")+"\"",budget,delegate(IntPtr s){rows.Add(Row(s,budget));});
      records+=rows.Count;WriteRows(writer,rows,budget);
     }
     writer.Flush();budget.Check();string digest;
     using(var sha=SHA256.Create()){content.Position=0;digest=BitConverter.ToString(sha.ComputeHash(content)).Replace("-","");}
     Query(db,"ROLLBACK",budget,delegate(IntPtr s){});budget.Check();
     return new Fingerprint{Digest=digest,Tables=names.Count,Rows=records,SqliteVersion=Marshal.PtrToStringAnsi(sqlite3_libversion()),ElapsedMs=budget.Clock.ElapsedMilliseconds};
    }
   } catch(Exception e){failure=e;throw;}
   finally {
    if(db!=IntPtr.Zero){sqlite3_progress_handler(db,0,null,IntPtr.Zero);int rc=sqlite3_close_v2(db);if(rc!=0){var close=new IOException("Synthetic SQLite snapshot close failed: sqliteCode="+rc);if(failure!=null)throw new AggregateException(failure,close);throw close;}}
    GC.KeepAlive(progress);
   }
  }
 }
}
'@
}

function Get-AcceptanceSqliteSnapshot {
    param([Parameter(Mandatory = $true)][string]$Path,
        [ValidateRange(1, 300)][int]$TimeoutSeconds = 30)
    $absolute = [IO.Path]::GetFullPath($Path)
    # Any load/open/read/integrity/deadline failure propagates. Never use a file
    # hash, empty digest or constant sentinel as a fallback for an active DB.
    [RigarusAcceptanceSqlite.Snapshot]::Read($absolute, $TimeoutSeconds)
}
