# Reference
# https://gist.github.com/johnlane/351adff97df196add08a

import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk, Gdk, GdkX11

import Xlib.X
import Xlib.display

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

        self.monitor_n = 2
        """ The monitor number """

        self.location:Bar.Location = Bar.Location.TOP

        # Colour style for (b)
        self.stylesheet = b"""
            window#bar {
                background-color: darkred;
            }
        """

        # Display > Screen > Monitor > Window
        self.window:Gtk.Window = None

        self.screen:GdkX11.X11Screen = None
        self.display:GdkX11.X11Display = None
        self.monitor:GdkX11.X11Monitor = None


    @property
    def xid(self):
        """ Can only be accessed after .show_all() """
        # Reference used instead: self.window.get_toplevel().get_window().get_xid()
        # self.window.get_window() is type GdkX11.X11Window (only exists after show_all I think)
        return self.window.get_window().get_xid()


    def create_window(self):
        # Version information
        print("Gtk %d.%d.%d" % (Gtk.get_major_version(),
                                Gtk.get_minor_version(),
                                Gtk.get_micro_version()))


        # Create an undecorated dock
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

        # The screen that the window is inside of
        # Usually only one screen nowadays which contains all the monitors
        # Gdk.Screen.get_default() seems to return the same screen, so I assume GTK 
        # uses the default screen for the window.
        # Also `self.display.get_default_screen()`
        self.screen = self.window.get_screen()
        print("screen", self.screen)

        # the screen contains all monitors
        self.display = self.screen.get_display()
        print("display", self.display)

        # (b) Style it
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(self.stylesheet)
        Gtk.StyleContext.add_provider_for_screen(
            self.screen,
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.set_monitor()

        # it must be shown before changing properties 
        self.window.show_all()

        print("xid", self.xid)
        print("getwindow2", self.window.get_window())


        self.set_location()





        # main event loop
        # Gtk.main()
        # Control-C termination broken in GTK3 http://stackoverflow.com/a/33834721
        # https://bugzilla.gnome.org/show_bug.cgi?id=622084
        from gi.repository import GLib
        GLib.MainLoop().run()


    def set_monitor(self):
        """
            Sets the monitor by moving the Gtk Window to the top left coordinate of the monitor.
        """

        self.monitor = self.display.get_monitor(self.monitor_n)
        print("monitor", self.monitor)
        self.monitor_geom = self.monitor.get_geometry()
        print("monitor_geom", self.monitor_geom)

        x = self.monitor_geom.x
        y = self.monitor_geom.y
        w = self.monitor_geom.width
        h = self.monitor_geom.height

        print(f"monitor {self.monitor_n}: ({x},{y}) ({w}x{h})")
        print(f"bar: start={x}, end={x+w-1}")

        # Resize monitor to be as wide and monitor and `bar_size` high
        self.window.resize(w, self.bar_size)

        # Move to top-left coordinate of desired monitor
        # Note this does NOT set the location (top/bottom) - see Bar.set_location for details
        self.window.move(x,y)

        # We might want to show the available monitors at one point
        # monitor_n = self.display.get_n_monitors()


    def set_location(self):
        """
            Moves the bar to the top or bottom of screen.


            When setting the coordinate with Window.move, GDK seems to try to place the dock at 
            a certain location (top or bottom) depending on this move coordinate (presumably based
            on whether the bar is closer to the top or bottom). However, when using multiple 
            monitors in particular arrangements this stops working reliably.

            In my case, I have 4 1080p monitors in the following upside-down "T" top-left coord arrangement:
                0. (3840,1080)
                1. (1920,1080)
                2. (0,1080)
                3. (1920,0)
            
            Setting the coordinate to (0,1080) places the bar at the bottom of the left screen rather than
            the top, even though it is closer to the top.
            
            To fix this, we manually set the X11 property "STRUT" and "STRUT_PARTIAL" on the window, which
            are essentially used to tell the WM to add gaps between the sides of monitors for applications
            like docks or status bars.

            STRUT: https://specifications.freedesktop.org/wm-spec/1.3/ar01s05.html
        """

        # Get X Display object so we can set low-level X properties (not Gdk)
        x_display:Xlib.display.Display = Xlib.display.Display()

        # X Window resource (not Gtk or Gdk)
        x_window = x_display.create_resource_object('window', self.xid)

        # Construct strut per the docs
        # https://specifications.freedesktop.org/wm-spec/1.3/ar01s05.html
        strut = [0 for i in range(12)]
        if self.location == Bar.Location.TOP:
            strut[2] = 0 + self.bar_size
            strut[8] = self.monitor_geom.x
            strut[9] = self.monitor_geom.x + self.monitor_geom.width - 1
        elif self.location == Bar.Location.BOTTOM:
            strut[3] = 0 + self.bar_size
            strut[10] = self.monitor_geom.x
            strut[11] = self.monitor_geom.x + self.monitor_geom.width - 1


        # Set STRUT_PARTIAL and STRUT properties on Xlib window

        _STRUT_PARTIAL = x_display.intern_atom('_NET_WM_STRUT_PARTIAL')
        _CARDINAL = x_display.intern_atom('CARDINAL')
        x_window.change_property(_STRUT_PARTIAL, _CARDINAL, 32, strut, Xlib.X.PropModeReplace)

        # WM should ignore STRUT if STRUT_PARTIAL is set, but i3 seems to need both.
        # For some reason this doesn't work reusing the _CARDINAL define above, so we redefine it here
        _STRUT = x_display.intern_atom('_NET_WM_STRUT')
        _CARDINAL = x_display.intern_atom('CARDINAL')
        x_window.change_property(_STRUT, _CARDINAL, 32, strut[:4], Xlib.X.PropModeReplace)


        # (d) reserve space (a "strut") for the bar so it does not become obscured
        #     when other windows are maximized, etc
        # http://stackoverflow.com/questions/33719686  property_change not in gtk3.0
        # https://sourceforge.net/p/python-xlib/mailman/message/27574603
        #
        #
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




if __name__ == "__main__":
    bar = Bar()
    bar.create_window()

