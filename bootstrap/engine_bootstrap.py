#
# Copyright (c) 2013 Shotgun Software, Inc
# ----------------------------------------------------
#
import os
import sys
import logging
import logging.handlers


# platform specific alert with no dependencies
def msgbox(msg):
    if sys.platform == "win32":
        import ctypes
        MessageBox = ctypes.windll.user32.MessageBoxA
        MessageBox(None, msg, "Shotgun", 0)
    elif sys.platform == "darwin":
        os.system("""osascript -e 'tell app "System Events" to activate""")
        os.system("""osascript -e 'tell app "System Events" to display dialog "%s" with icon caution buttons "Sorry!"'""" % msg)

# setup logging
################################################################################
try:
    log_dir = '%s/Library/Logs/Shotgun/' % os.path.expanduser('~')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    rotating = logging.handlers.RotatingFileHandler(os.path.join(log_dir, 'tk-photoshop.log'), maxBytes=4*1024*1024, backupCount=10)
    rotating.setFormatter(logging.Formatter('%(asctime)s [%(levelname) 8s] %(threadName)s %(name)s: %(message)s'))
    logger = logging.getLogger('tank')
    logger.addHandler(rotating)
    logger.setLevel(logging.INFO)

    logger = logging.getLogger('tank.photoshop.PythonBootstrap')
    logger.info('================================== Initializing Python Interpreter ===================================')

    # setup default exception handling to log
    def logging_excepthook(type, value, tb):
        logger.exception("Uncaught exception", exc_info=(type, value, tb))
        sys.__excepthook__(type, value, tb)
    sys.execpthook = logging_excepthook
except Exception, e:
    msgbox("Shotgun pipeline toolkit failed to initialize logging:\n\n%s" % e)
    raise

# setup sys path to include photoshop API
################################################################################
api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python"))
sys.path.insert(0, api_path)

# initalize photoshop
try:
    import photoshop
    import photoshop_extension_manager
    logger.debug(sys.argv)
    remote_port = int(sys.argv[1])
    photoshop.initialize_photoshop_application(remote_port)
    # if we made it here, tag the extension version
    photoshop_extension_manager.tag()
except Exception, e:
    msgbox("Shotgun pipeline toolkit failed to initialize photoshop api:\n\n%s" % e)
    logger.exception('Failed to initialize photoshop api')
    sys.exit(1)


# Startup PySide
################################################################################
try:
    from PySide import QtGui
    from tk_photoshop import logging_console
except Exception, e:
    msgbox("Shotgun pipeline toolkit failed to initialize PySide.  Is it installed?")
    logger.exception("Failed to initialize PySide.")
    sys.exit(1)

g_resourceDir = os.path.join(os.path.dirname(__file__), "..", "resources")

# create global app
try:
    sys.argv[0] = 'Shotgun Photoshop'
    QtGui.QApplication.setStyle("cleanlooks")
    g_app = QtGui.QApplication(sys.argv)
    g_app.setQuitOnLastWindowClosed(False)
    g_app.setWindowIcon(QtGui.QIcon(os.path.join(g_resourceDir, "app.png")))
    g_app.setApplicationName(sys.argv[0])
except Exception, e:
    msgbox("Could not create global PySide app:\n\n%s" % e)
    logger.exception("Could not create global PySide app")
    sys.exit(1)

# update style
try:
    css_file = os.path.join(g_resourceDir, "dark.css")
    f = open(css_file)
    css = f.read()
    f.close()
    g_app.setStyleSheet(css)
except Exception:
    logger.exception("Could not set QT style sheet")

# logging console
try:
    g_log = logging_console.LogConsole()
    g_app.setProperty("tk-photoshop.log_console", g_log)
    qt_handler = logging_console.QtLogHandler(g_log.logs)
    logger = logging.getLogger('tank')
    logger.addHandler(qt_handler)
    g_log.setHidden(True)
except Exception, e:
    msgbox("Could not create logging console:\n\n%s" % e)
    logger.exception("Could not create logging console")
    sys.exit(1)


# run userSetup.py if it exists, borrowed from Maya
################################################################################
try:
    for path in sys.path:
        scriptPath = os.path.join(path, 'userSetup.py')
        if os.path.isfile(scriptPath):
            logger.debug('Running "%s"', scriptPath)
            import __main__
            try:
                execfile(scriptPath, __main__.__dict__)
            except:
                logger.exception('Error running "%s"', scriptPath)
except Exception, e:
    logger.exception('Failed to execute userSetup.py')

logger.info("Starting PySide backend application %s", g_app)
sys.exit(g_app.exec_())
