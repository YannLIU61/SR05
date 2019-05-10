
if __name__ == "__main__":
    import sys
    import fcntl
    import os

    # set sys.stdin non-blocking
    orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

    from ui.asyncio_window import AsyncIOWindow

    window = AsyncIOWindow()
    window.mainloop()


