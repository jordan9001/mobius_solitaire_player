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

                int scount = 0;
                Console.WriteLine("{0,16} {1,16} {2,8} {3}", "Object", "MethodTable", "Size", "Type");
                foreach (ClrObject obj in heap.EnumerateObjects())
                {
                    if (obj.IsFree)
                    {
                        continue;
                    }
                    var tn = obj.Type;
                    if (tn.Name != "SolitaireItem")
                    {
                        continue;
                    }
                    scount += 1;

                    /*
                     * Awesome, the SolitaireItems are part of a null terminated doubly linked list, with 4 of the Items not being cards, but being the stacks themselves at the "top"
                     * Suit = +0xc [ 4 bytes ]
                     * CardType = +0x10 [ 4 bytes ] 1=A .. 9=9 10=a J=b ..
                     * SomeXPos = +0x28 [ 4 bytes ]
                     * SomeYPos = +0x2C [ 4 bytes ]
                     * UpLink = +0x30
                     * DownLink = +0x40
                     */

                    //Console.WriteLine($"{obj.Address:x16} {obj.Type.MethodTable:x16} {obj.Size,8:D} {obj.Type.Name}");
                    IntPtr numbytes = (IntPtr)0;
                    ulong sz = obj.Size;
                    if (sz > 0x400)
                    {
                        sz = 0x400;
                    }
                    byte[] buf = new byte[sz];
                    ReadProcessMemory(ph, (IntPtr)obj.Address, buf, (int)obj.Size, out numbytes);
                    uint suit = BitConverter.ToUInt32(buf, 0xc);
                    uint card = BitConverter.ToUInt32(buf, 0x10);
                    uint somex = BitConverter.ToUInt32(buf, 0x28);
                    uint somey = BitConverter.ToUInt32(buf, 0x2c);
                    Console.WriteLine($"{card}[{suit}] @ {somex:x4},{somey:x4}");

                    // Dump bytes
                    /*
                    for (ulong i = 0; i < sz; i++)
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
                    */
                }
                Console.WriteLine("Saw {0} items", scount);
            }
            return;
        }
    }
}
