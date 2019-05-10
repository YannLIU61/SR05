import sys
import fcntl
import os
import argparse
import socket

if __name__ == "__main__":
    # set sys.stdin non-blocking
    orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

    from ui.node import NodeWindow
    from protocol.ptl import SR05Encoder, SR05Decoder, Encoder, Decoder

    parser = argparse.ArgumentParser(description='Un noeud de system reparti')
    parser.add_argument('--auto', dest='auto_mode', action="store_true", help='Lancer en mode auto')
    parser.add_argument('--ident', dest='ident', nargs=1, default=socket.gethostname(), help='Identifieur de machine')

    args = parser.parse_args()

    window = NodeWindow(ident=args.ident[0] if isinstance(args.ident, list) else args.ident, decoder=SR05Decoder(), encoder=SR05Encoder(), auto_mode=args.auto_mode)
    window.mainloop()

