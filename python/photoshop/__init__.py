#
# Copyright (c) 2013 Shotgun Software, Inc
# ----------------------------------------------------
#
# system modules
import sys
import logging

# local modules
import flexbase

# setup logging
################################################################################
logger = logging.getLogger('tank.photoshop')


def log_debug(msg, *args, **kwargs):
    logger.debug(msg, *args, **kwargs)


def log_error(msg, *args, **kwargs):
    logger.error(msg, *args, **kwargs)


def log_exception(msg, *args, **kwargs):
    logger.exception(msg, *args, **kwargs)


# setup default exception handling to log
def logging_excepthook(type, value, tb):
    logger.exception("Uncaught exception", exc_info=(type, value, tb))
    sys.__excepthook__(type, value, tb)
sys.execpthook = logging_excepthook


# setup actionscript integration
################################################################################
def clear_panel():
    flexbase.requestClearPanel()


def add_button(label, callback):
    flexbase.requestAddButton(label, callback)


def RemoteObject(cls, *args, **kwargs):
    return flexbase.RemoteObject(cls, *args, **kwargs)


# plugin initialization will call the app setup
def initialize_photoshop_application(remote_port):
    global app
    try:
        flexbase.setup(remote_port)
        app = flexbase.requestStatic('com.adobe.csawlib.photoshop.Photoshop', 'app')
        logger.info("Photoshop version is '%s'", app.version)
    except:
        log_exception('error in initializePhotoshopApplication')


# setup gui utilities
################################################################################
def messageBox(text):
    try:
        from tank.platform.qt import QtGui, QtCore
        msg = QtGui.QMessageBox()
        msg.setText(text)
        msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        return msg.exec_()
    except Exception:
        log_exception("messageBox failed")