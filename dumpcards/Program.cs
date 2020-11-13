using System;
using System.Diagnostics;
using Microsoft.Diagnostics.Runtime;
using System.Runtime.InteropServices;

namespace dumpcards
{
    class Program
    {
        [DllImport("kernel32.dll")]
        public static extern bool ReadProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, int dwSize, out IntPtr lpNumberOfBytesRead);

        static void Main(string[] args)
        {
            int processId = -1;
            Process[] parr = Process.GetProcessesByName("Möbius Front '83");
            if (parr.Length != 1)
            {
                Console.WriteLine("Unable to find unique game process");
                Environment.Exit(-1);
            }
            IntPtr ph = parr[0].Handle;
            DataTarget targ = DataTarget.AttachToProcess(parr[0].Id, suspend: false);
        
            foreach (ClrInfo clr in targ.ClrVersions)
            {
                Console.WriteLine("Found CLR version: " + clr.Version);

                using ClrRuntime runtime = clr.CreateRuntime();
                ClrHeap heap = runtime.Heap;

                Console.WriteLine("{0,16} {1,16} {2,8} {3}", "Object", "MethodTable", "Size", "Type");
                foreach (ClrObject obj in heap.EnumerateObjects())
                {
                    var tn = obj.Type;
                    if (tn.Name == "GameLogic")
                    {
                        Console.WriteLine($"{obj.Address:x16} {obj.Type.MethodTable:x16} {obj.Size,8:D} {obj.Type.Name}");
                        IntPtr numbytes = (IntPtr)0;
                        byte[] buf = new byte[obj.Size];
                        ReadProcessMemory(ph, (IntPtr)obj.Address, buf, (int)obj.Size, out numbytes);

                        for (ulong i = 0; i < obj.Size; i++)
                        {
                            Console.Write("{0:x2} ", buf[i]);
                            if (0 == ((i+1) % 16))
                            {
                                Console.WriteLine();
                            }
                            else if (0 == ((i+1) % 8))
                            {
                                Console.Write(" ");
                            }
                        }
                        Console.WriteLine();
                    }
                }
            }
        }
    }
}
