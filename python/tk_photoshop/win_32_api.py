#
# Copyright (c) 2013 Shotgun Software, Inc
# ----------------------------------------------------
#
"""
minimal set of win32 functions used by photoshop engine to manage tank UI under windows
"""
import ctypes
from ctypes import wintypes

# user32.dll
EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
SendMessage = ctypes.windll.user32.SendMessageW
SendMessageTimeout = ctypes.windll.user32.SendMessageTimeoutW
GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
SetParent = ctypes.windll.user32.SetParent
RealGetWindowClass = ctypes.windll.user32.RealGetWindowClassW
EnableWindow = ctypes.windll.user32.EnableWindow
IsWindowEnabled = ctypes.windll.user32.IsWindowEnabled

# kernal32.dll
CloseHandle = ctypes.windll.kernel32.CloseHandle
CreateToolhelp32Snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot
Process32First = ctypes.windll.kernel32.Process32FirstW
Process32Next = ctypes.windll.kernel32.Process32NextW

# some defines
TH32CS_SNAPPROCESS = 0x00000002
WM_GETTEXT = 0x000D
SMTO_ABORTIFHUNG = 0x0002
SMTO_BLOCK = 0x0001

# structures
class PROCESSENTRY32(ctypes.Structure):
     _fields_ = [("dwSize", ctypes.wintypes.DWORD),
                 ("cntUsage", ctypes.wintypes.DWORD),
                 ("th32ProcessID", ctypes.wintypes.DWORD),
                 ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                 ("th32ModuleID", ctypes.wintypes.DWORD),
                 ("cntThreads", ctypes.wintypes.DWORD),
                 ("th32ParentProcessID", ctypes.wintypes.DWORD),
                 ("pcPriClassBase", ctypes.c_long),
                 ("dwFlags", ctypes.wintypes.DWORD),
                 ("szExeFile", ctypes.c_wchar * ctypes.wintypes.MAX_PATH)]

def find_parent_process_id(process_id):
    """
    Find the parent process id for a given process
    :param process_id: id of process to find parent of
    :returns: parent process id or None if parent not found
    """
    parent_process_id = None
    try:
        h_process_snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
 
        pe = PROCESSENTRY32()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
        
        ret = Process32First(h_process_snapshot, ctypes.byref(pe))
        while ret:
            if pe.th32ProcessID == process_id:
                parent_process_id = pe.th32ParentProcessID
                break
            ret = Process32Next(h_process_snapshot, ctypes.byref(pe))
    except Exception, e:
        pass
    else:
        CloseHandle(h_process_snapshot)
        
    return parent_process_id

def safe_get_window_text(hwnd):
    """
    Safely get the window text (title) of a specified window
    :param hwnd: window handle to get the text of
    :returns: window title if found
    """
    title = ""
    try:
        buffer_sz = 1024
        buffer = ctypes.create_unicode_buffer(buffer_sz)
        result = SendMessageTimeout(hwnd, WM_GETTEXT, buffer_sz, ctypes.byref(buffer),
                                            SMTO_ABORTIFHUNG | SMTO_BLOCK, 100, 0)
        if result != 0:
            title = buffer.value
    except Exception, e:
        pass
    return title
        
def find_windows(process_id = None, class_name = None, window_text = None, stop_if_found = True):
    """
    Find top level windows matching certain criteria
    :param process_id: only match windows that belong to this process id if specified
    :param class_name: only match windows that match this class name if specified
    :param window_text: only match windows that match this window text if specified
    :param stop_if_found: stop when find a match
    :returns: list of window handles found by search
    """
    found_hwnds = []

    # sub-function used to actually enumerate the windows in EnumWindows
    def enum_windows_proc(hwnd, lparam):
        # try to match process id:
        matches_proc_id = True
        if process_id != None:
            win_process_id = ctypes.c_long()      
            GetWindowThreadProcessId(hwnd, ctypes.byref(win_process_id))
            matches_proc_id = (win_process_id.value == process_id)
        if not matches_proc_id:
            return True
        
        # try to match class name:
        matches_class_name = True
        if class_name != None:
            buffer_len = 1024
            buffer = ctypes.create_unicode_buffer(buffer_len)
            RealGetWindowClass(hwnd, buffer, buffer_len)
            matches_class_name = (class_name == buffer.value)
        if not matches_class_name:
            return True
        
        # try to match window text:
        matches_window_text = True
        if window_text != None:
            hwnd_text = safe_get_window_text(hwnd)
            matches_window_text = (window_text in hwnd_text)
        if not matches_window_text:
            return True
        
        # found a match    
        found_hwnds.append(hwnd)
        
        return not stop_if_found
            
    # enumerate all top-level windows:
    EnumWindows(EnumWindowsProc(enum_windows_proc), None)
    
    return found_hwnds

def qwidget_winid_to_hwnd(id):
    """
    Convert the winid for a qtwidget to a HWND
    :param id: qtwidget winid to convert
    :returns: window handle
    """
    # Setup arguments and return types
    ctypes.pythonapi.PyCObject_AsVoidPtr.restype = ctypes.c_void_p
    ctypes.pythonapi.PyCObject_AsVoidPtr.argtypes = [ ctypes.py_object ]
 
    # Convert PyCObject to a void pointer
    hwnd = ctypes.pythonapi.PyCObject_AsVoidPtr(id)
    
    return hwnd
