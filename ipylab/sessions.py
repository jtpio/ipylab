from collections import defaultdict
from ipywidgets import Widget, register, widget_serialization
from traitlets import List, Unicode, Bool, Instance, HasTraits, Dict

from ._frontend import module_name, module_version


def _noop():
    pass


class Kernel(HasTraits):
    '''Maps Kernel.IModel
    
    TODO: Not Used Currently
    '''
    _id = Unicode(readonly=True)
    name = Unicode(readonly=True)


class KernelPreference(HasTraits):
    '''Maps ISessionContext.IKernelPreference
    
    TODO: Not Used Currently
    '''
    _id = Unicode(read_only=True)
    name = Unicode(read_only=True)
    language = Unicode(read_only=True)
    shouldStart = Bool(True, read_only=True)
    canStart = Bool(True, read_only=True)
    shutdownOnDispose = Bool(False, read_only=True)
    autoStartDefault = Bool(True, read_only=True)


class SessionContext(HasTraits):
    '''Partially Map @jupyterlab/apputils SessionContext.IOptions

    TODO: Not Used Currently
    '''
    path = Unicode(read_only=True)
    basePath = Unicode(read_only=True)
    name = Unicode(read_only=True)
    kernelPreference = Instance(KernelPreference).tag(**widget_serialization)


class Session(HasTraits):
    '''Maps @jupyterlab/services Session.IModel

    TODO: Not Used Currently
    '''
    _id = Unicode(readonly=True)
    name = Unicode(readonly=True)
    path = Unicode(readonly=True)
    _type = Unicode(readonly=True)
    kernel = Instance(Kernel).tag(**widget_serialization)


@register
class SessionManager(Widget):
    '''Expose JupyterFrontEnd.serviceManager.sessions'''
    _model_name = Unicode("SessionManagerModel").tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)

    # keeps track of alist of sessions
    current_session = Dict(read_only=True).tag(sync=True)
    sessions = List([], read_only=True).tag(sync=True)

    def get_current_session(self):
        '''Force a call to update current session'''
        self.send({"func":"get_current"})

    def list_sessions(self):
        '''List all running sessions managed in the manager'''
        return self.sessions