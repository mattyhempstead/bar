# Reference
# https://gist.github.com/johnlane/351adff97df196add08a

import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk, Gdk, GdkX11

import Xlib
from Xlib.display import Display
from Xlib import X

from enum import Enum, auto


class Bar:

    class Location(Enum):
        TOP = auto()
        BOTTOM = auto()

    def __init__(self):

        self.bar_title = "barrr"
        """ The X11 window title for the bar """

        self.bar_size = 50
        """ The height of the bar in pixels """

        self.location = Bar.Location.TOP

        # Colour style for (b)
        self.stylesheet = b"""
            window#bar {
                background-color: darkred;
            }
        """

        self.window = None


    def create_window(self):
        # Version information
        print("Gtk %d.%d.%d" % (Gtk.get_major_version(),
                                Gtk.get_minor_version(),
                                Gtk.get_micro_version()))

        # (a) Create an undecorated dock
        self.window = Gtk.Window()

        # X11 title
        self.window.set_title(self.bar_title)

        # Setting a name gives the window a CSS #id
        self.window.set_name("bar")

        # The window manager will use the type hint of DOCK to apply certain attributes
        """
            In the case of i3 I stuff like
             - inability to select window (using cursor or keyboard)
             - static size and no tiling
        """
        self.window.set_type_hint(Gdk.WindowTypeHint.DOCK)

        """
            Remove decorations like title bar, resize controls, i3 window border, etc.
            Seems like the DOCK type hint already applies this.
        """
        self.window.set_decorated(False)

        """ Quit if user requests """
        self.window.connect("delete-event", Gtk.main_quit)


        print("window", self.window)
        print(self.window.get_window())
        # print(window.get_window().get_xid())

        # (b) Style it
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(self.stylesheet)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # the screen contains all monitors
        screen = self.window.get_screen()
        print(screen)
        # print(dir(screen))
        # input()

        monitor = self.window.get_monitor()
        print("mon", monitor)

        # width = screen.width() # width = Gdk.Screen.width()
        # print("width: %d" % width)

        display = screen.get_display()
        print("display", display)

        print("default screen", display.get_default_screen())
        # print(display.get_())

        print(dir(screen.get_display()))
        input()

        # (c) collect data about each monitor
        monitors = []
        nmons = screen.get_display().get_n_monitors()
        print("there are %d monitors" % nmons)
        for m in range(nmons):
            monitor = display.get_monitor(m)
            print(monitor)
            print(monitor.get_geometry())
            mg = monitor.get_geometry()
            print("monitor %d: %d x %d" % (m,mg.width,mg.height))
            monitors.append(mg)

        print(monitors)

        curmon = 0

        # current monitor
        # curmon = screen.get_monitor_at_window(screen.get_active_window())
        x = monitors[curmon].x
        y = monitors[curmon].y
        width = monitors[curmon].width
        height = monitors[curmon].height
        print("monitor %d: %d x %d (current, offset %d)" % (curmon,width,height,x))
        print("bar: start=%d end=%d" % (x,x+width-1))

        # display bar along the top of the current monitor
        # y = 100

        # print("width: %d" % width)

        print("move", x, y)
        # window.move(x,y)
        self.window.move(x,y+height/2-1)

        # 
        self.window.resize(10, self.bar_size)
        # window.resize(width, self.bar_size)

        # it must be shown before changing properties 
        self.window.show_all()

        # (d) reserve space (a "strut") for the bar so it does not become obscured
        #     when other windows are maximized, etc
        # http://stackoverflow.com/questions/33719686  property_change not in gtk3.0
        # https://sourceforge.net/p/python-xlib/mailman/message/27574603
        # display = Display()
        # xid = window.get_toplevel().get_window().get_xid()
        # print("xid", hex(xid))
        # topw = display.create_resource_object('window', xid)

        # # http://python-xlib.sourceforge.net/doc/html/python-xlib_21.html#SEC20
        # topw.change_property(display.intern_atom('_NET_WM_STRUT'),
        #                        display.intern_atom('CARDINAL'), 32,
        #                        [0, 0, self.bar_size, 0 ],
        #                        X.PropModeReplace)
        # topw.change_property(display.intern_atom('_NET_WM_STRUT_PARTIAL'),
        #                        display.intern_atom('CARDINAL'), 32,
        #                        [0, 0, self.bar_size, 0, 0, 0, 0, 0, x, x+width-1, 0, 0],
        #                        X.PropModeReplace)

        # we set _NET_WM_STRUT, the older mechanism as well as _NET_WM_STRUT_PARTIAL
        # but window managers ignore the former if they support the latter.
        #
        # the numbers in the array are as follows:
        #
        # 0, 0, self.bar_size, 0 are the number of pixels to reserve along each edge of the
        # screen given in the order left, right, top, bottom. Here the size of the bar
        # is reserved at the top of the screen and the other edges are left alone.
        #
        # _NET_WM_STRUT_PARTIAL also supplies a further four pairs, each being a
        # start and end position for the strut (they don't need to occupy the entire
        # edge).
        #
        # In the example, we set the top start to the current monitor's x co-ordinate
        # and the top-end to the same value plus that monitor's width, deducting one.
        # because the co-ordinate system starts at zero rather than 1. The net result
        # is that space is reserved only on the current monitor.
        #
        # co-ordinates are specified relative to the screen (i.e. all monitors together).
        #


        # main event loop
        # Gtk.main()
        # Control-C termination broken in GTK3 http://stackoverflow.com/a/33834721
        # https://bugzilla.gnome.org/show_bug.cgi?id=622084
        from gi.repository import GLib
        GLib.MainLoop().run()


    def set_monitor(self):
        pass



if __name__ == "__main__":
    bar = Bar()
    bar.create_window()


