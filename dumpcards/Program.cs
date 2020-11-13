using System;
using System.Diagnostics;
using System.Collections.Generic;
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
            Process[] parr = Process.GetProcessesByName("Möbius Front '83");
            if (parr.Length != 1)
            {
                Console.Error.WriteLine("Unable to find unique game process");
                Environment.Exit(-1);
            }
            IntPtr ph = parr[0].Handle;
            DataTarget targ = DataTarget.AttachToProcess(parr[0].Id, suspend: false);
        
            foreach (ClrInfo clr in targ.ClrVersions)
            {
                Console.Error.WriteLine("Found CLR version: " + clr.Version);

                using ClrRuntime runtime = clr.CreateRuntime();
                ClrHeap heap = runtime.Heap;

                var yset = new SortedSet<uint>();
                var xset = new SortedSet<uint>();
                var cardList = new List<(uint, uint, uint)>();

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

                    /*
                     * Awesome, the SolitaireItems are part of a null terminated doubly linked list, with 4 of the Items not being cards, but being the stacks themselves at the "top"
                     * Suit = +0xc [ 4 bytes ]
                     * CardType = +0x10 [ 4 bytes ] 1=A .. 9=9 10=a J=b ..
                     * SomeXPos = +0x28 [ 4 bytes ]
                     * SomeYPos = +0x2C [ 4 bytes ]
                     * UpLink = +0x30
                     * DownLink = +0x40
                     */
                    //TODO detect which cards are in play, and which are left over from previous game but not gc'd yet?

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

                    if (card != 0)
                    {
                        yset.Add(somey);
                        xset.Add(somex);
                        cardList.Add((card, somex, somey));
                    }

                    // Dump bytes of aces to try and figure out diff between used cards and unused
                    if (card == 1)
                    {
                        Console.Error.WriteLine($"{card}[{suit}] @ {somex:x4},{somey:x4}");
                        for (ulong i = 0; i < sz; i++)
                        {
                            Console.Error.Write("{0:x2} ", buf[i]);
                            if (0 == ((i + 1) % 16))
                            {
                                Console.Error.WriteLine();
                            }
                            else if (0 == ((i + 1) % 8))
                            {
                                Console.Error.Write(" ");
                            }
                        }
                        Console.Error.WriteLine();
                    }

                }

                if (cardList.Count != 52)
                {
                    Console.Error.WriteLine("Got {0} cards", cardList.Count);
                    return;
                }

                if (xset.Count != 4 || yset.Count != 13)
                {
                    Console.Error.WriteLine("Not in Beginning of solitaire game, {0} x positions and {1} y positions", xset.Count, yset.Count);
                    return;
                }

                foreach (var c in cardList)
                {
                    uint xi = 0;
                    uint yi = 0;

                    foreach (var xp in xset)
                    {
                        if (xp == c.Item2)
                        {
                            break;
                        }
                        xi++;
                    }

                    foreach (var yp in yset)
                    {
                        if (yp == c.Item3)
                        {
                            break;
                        }
                        yi++;
                    }

                    Console.WriteLine($"{c.Item1} {xi} {12 - yi}");
                }
            }
            return;
        }
    }
}
