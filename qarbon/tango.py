# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# This file is part of qarbon (http://qarbon.rtfd.org/)
#
# Copyright (c) 2013 European Synchrotron Radiation Facility, Grenoble, France
#
# Distributed under the terms of the GNU Lesser General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ----------------------------------------------------------------------------

"""Tango plugin for qarbon."""

import weakref
import functools

import PyTango as Tango

from qarbon import log
from qarbon.external.pint import Quantity
from qarbon.executor import task
from qarbon.core import Factory as _Factory
from qarbon.core import Database as _Database
from qarbon.core import Device as _Device
from qarbon.core import Attribute as _Attribute
from qarbon.core import Quality, Access, DisplayLevel
from qarbon.core import AttributeConfig, AttributeValue

__NO_STR_VALUE = Tango.constants.AlrmValueNotSpec, Tango.constants.StatusNotSet

# The exception reasons that will force switching from events to polling
# API_AttributePollingNotStarted - the attribute does not support events. 
#                                  Don't try to resubscribe.
# API_DSFailedRegisteringEvent - same exception then the one above but higher
#                                in the stack
# API_NotificationServiceFailed - Problems in notifd, it was not able to
#                                 register the event.
# API_EventChannelNotExported - the notifd is not running
# API_EventTimeout - after a successfull register the the device server 
#                    and/or notifd shuts down/crashes
# API_CommandNotFound - Added on request from ESRF (Matias Guijarro). They have
#                       a DS in java (doesn't have events) and the only way they
#                       found to fix the event problem was to add this exception
#                       type here. Maybe in future this will be solved in a better
#                       way
# API_BadConfigurationProperty - the device server is not running
EVENT_TO_POLLING_EXCEPTIONS = set(
    ('API_AttributePollingNotStarted',
     'API_DSFailedRegisteringEvent',
     'API_NotificationServiceFailed',
     'API_EventChannelNotExported',
     'API_EventTimeout',
     'API_EventPropertiesNotSet',
     'API_CommandNotFound',))
#                                   'API_BadConfigurationProperty') 

def quantity_t2q(value, units=None, fmt=None):
    if value is None:
        return None
    res = Quantity(value, units=units)
    if fmt is not None:
        res.default_format = fmt + res.default_format
    return res


def quantity_str2t(value_str, dtype=None, units=None, fmt=None):
    return quantity_t2q(Tango.str_2_obj(value_str, dtype), units=units, fmt=fmt)


def quantity_str2t_no_error(value_str, dtype=None, units=None, fmt=None):
    try:
        return quantity_str2t(value_str, dtype=dtype, units=units, fmt=fmt)
    except ValueError:
        pass


def __base_unit_t2q(unit, null, to_quantity=True):
    if to_quantity:
        if unit == null or unit is None:
            return None
        unit = Quantity(unit)
    else:    
        if unit == null or unit is None:
            unit = None
    return unit


def unit_t2q(unit, to_quantity=True):
    return __base_unit_t2q(unit, Tango.constants.UnitNotSpec,
                           to_quantity=to_quantity)


def display_unit_t2q(unit, to_quantity=True):
    return __base_unit_t2q(unit, Tango.constants.DispUnitNotSpec,
                           to_quantity=to_quantity)


def standard_unit_t2q(unit, to_quantity=True):
    return __base_unit_t2q(unit, Tango.constants.StdUnitNotSpec,
                           to_quantity=to_quantity)


def ndim_t2q(data_format):
    return int(data_format)


def display_level_t2q(disp_level):
    return DisplayLevel(disp_level)


def access_t2q(access):
    return Access(access)


def quality_t2q(quality):
    return Quality(int(quality))


__NULL_DESC = Tango.constants.DescNotSet, Tango.constants.DescNotSpec
def description_t2q(desc):
    if desc in __NULL_DESC:
        desc = ''
    return desc

__S_TYPES = (Tango.CmdArgType.DevString,
    Tango.CmdArgType.DevVarStringArray,
    Tango.CmdArgType.DevEncoded,)
def standard_display_format_t2q(dtype, fmt):
    if fmt == 'Not specified':
        return '!s'
    
    # %6.2f is the default value that Tango sets when the format is
    # unassigned in tango < 8. This is only good for float types! So for other
    # types I am changing this value.
    if fmt == '%6.2f':
        if Tango.is_float_type(dtype, inc_array=True):
            pass
        elif Tango.is_int_type(dtype, inc_array=True):
            fmt = '%d'
        elif tango_cfg.data_type in __S_TYPES:
            fmt = '%s'
    return fmt


def display_format_t2q(dtype, fmt):
    fmt = standard_display_format_t2q(dtype, fmt)
    return fmt.replace('%s', '!s').replace('%r', '!r').replace('%', '')


def attr_config_t2q(tango_cfg):
    if tango_cfg is None:
        return None
    result = AttributeConfig()

    dtype = tango_cfg.data_type
    disp_fmt = display_format_t2q(dtype, tango_cfg.format)

    result.name = tango_cfg.name
    result.label = tango_cfg.label
    result.description = description_t2q(tango_cfg.description)
    result.ndim = int(tango_cfg.data_format)
    result.display_level = display_level_t2q(tango_cfg.disp_level)
    result.format = standard_display_format_t2q(dtype, tango_cfg.format)
    result.access = access_t2q(tango_cfg.writable)
    result.display_format = disp_fmt

    numerical = Tango.is_numerical_type(dtype)         

    result.unit = units = unit_t2q(tango_cfg.unit, to_quantity=numerical)
    result.display_unit = display_unit_t2q(tango_cfg.display_unit,
                                           to_quantity=numerical)
    result.standard_unit = standard_unit_t2q(tango_cfg.standard_unit,
                                             to_quantity=numerical)

    if numerical:
        Q_ = functools.partial(quantity_str2t_no_error, units=units,
                               dtype=dtype, fmt=disp_fmt)
    else:
        Q_ = functools.partial(Tango.str_2_obj, tg_type=dtype)
    result.min_value = Q_(tango_cfg.min_value)
    result.max_value = Q_(tango_cfg.max_value)
    result.min_alarm = Q_(tango_cfg.min_alarm)
    result.max_alarm = Q_(tango_cfg.max_alarm)
    result.min_warning = Q_(tango_cfg.alarms.min_warning)
    result.max_warning = Q_(tango_cfg.alarms.max_warning)
        
    result.value_range = [result.min_value, result.max_value]
    result.alarm_range = [result.min_alarm, result.max_alarm]
    result.warning_range = [result.min_warning, result.max_warning]

    # add dev_name, dev_alias, attr_name, attr_full_name
#    dev, attr = attr_cfg._getDev(), attr_cfg._getAttr()
#    result.dev_name = dev.getNormalName()
#    result.dev_alias = dev.getSimpleName()
#    result.attr_name = attr.getSimpleName()
#    result.attr_fullname = attr.getNormalName()
    return result


def attr_value_t2q(attr_cfg, tango_attr_value):
    if tango_attr_value.has_failed:
        pass
    else:
        if tango_attr_value.is_empty:
            pass

    dtype = tango_attr_value.type
    dformat = tango_attr_value.data_format
    fmt = attr_cfg.display_format
    numerical = Tango.is_numerical_type(dtype)

    r_value = tango_attr_value.value
    w_value = tango_attr_value.w_value
    units = attr_cfg.unit
    if numerical:
        if r_value is not None:
            r_value = Quantity(r_value, units=units)
            if fmt is not None:
                r_value.default_format = fmt + r_value.default_format
        if w_value is not None:
            w_value = Quantity(w_value, units=units)
            if fmt is not None:
                w_value.default_format = fmt + w_value.default_format
    
    r_ndim = 0
    if dformat == Tango.AttrDataFormat.SPECTRUM:
        r_ndim = 1
    elif dformat == Tango.AttrDataFormat.IMAGE:
        r_ndim = 2
    
    quality = quality_t2q(tango_attr_value.quality)
    value = AttributeValue(r_value=r_value, r_quality=quality, r_ndim=r_ndim,
                           r_timestamp=tango_attr_value.time.todatetime(),
                           w_value=w_value, config=attr_cfg)
    return value


def clone_attr_value(attr_cfg, attr_value):
    """ """
    r_value = attr_value.r_value
    r_quality = attr_value.r_quality
    r_ndim = attr_value.r_ndim
    r_timestamp = attr_value.r_timestamp
    w_value = attr_value.w_value
    fmt = attr_cfg.display_format
    if isinstance(r_value, Quantity):
        r_value = Quantity(r_value.magnitude, units=attr_cfg.unit)
        if fmt is not None:
            r_value.default_format = fmt + r_value.default_format
    if isinstance(w_value, Quantity):
        w_value = Quantity(w_value.magnitude, units=attr_cfg.unit)
        if fmt is not None:
            w_value.default_format = fmt + w_value.default_format
    value = AttributeValue(r_value=r_value, r_quality=r_quality, r_ndim=r_ndim,
                           r_timestamp=r_timestamp, w_value=w_value,
                           config=attr_cfg)
    return value

class TangoFuture(object):

    def __init__(self, future):
        self.__future = future
        self.__value = None

    def _get_value(self):
        if self.__value is None:
            value = self.__future.result()
            self.__value = self._decode(value)
        return self.__value


class TangoAttributeConfigFuture(AttributeConfig, TangoFuture):

    def __init__(self, attr_config_f):
        AttributeConfig.__init__(self)
        TangoFuture.__init__(self, attr_config_f)
    
    def _decode(self, attr_config):
        return attr_config_t2q(attr_config)

    @property
    def name(self):
        return self._get_value().name

    @property
    def label(self):
        return self._get_value().label

    @property
    def description(self):
        return self._get_value().description

    @property
    def ndim(self):
        return self._get_value().ndim

    @property
    def access(self):
        return self._get_value().access

    @property
    def display_format(self):
        return self._get_value().display_format

    @property
    def unit(self):
        return self._get_value().unit


class TangoAttributeValueFuture(AttributeValue, TangoFuture):

    def __init__(self, dev_attr_f, config=None):
        AttributeValue.__init__(self, config=config)
        TangoFuture.__init__(self, dev_attr_f)

    def _decode(self, dev_attr):
        return attr_value_t2q(self.config, dev_attr)

    @property
    def r_value(self):
        return self._get_value().r_value

    @property
    def r_ndim(self):
        return self._get_value().r_ndim
             
    @property
    def r_quality(self):
        return self._get_value().r_quality

    @property
    def r_timestamp(self):
        return self._get_value().r_timestamp

    @property
    def w_value(self):
        return self._get_value().w_value

    @property
    def exc_info(self):
        return self._get_value().exc_info

    @property
    def error(self):
        return self._get_value().error


class Database(_Database):

    def __init__(self, name, parent=None):
        _Database.__init__(self, name, parent=parent)
        self.__database = task(Tango.Database, name)

    def hw_database(self):
        return self.__database.result()

    def get_device(self, name):
        name = name.lower()
        device = self.get_child(name)
        if device is None:
            device = self.add_child(name, Device(name, parent=self))         
        return device
    

class Device(_Device):

    def __init__(self, name, parent=None):
        _Device.__init__(self, name, parent=parent)
        self.__device = task(Tango.DeviceProxy, name)

    @property
    def hw_device(self):
        return self.__device.result()

    def get_attribute(self, name):
        name = name.lower()
        attr = self.get_child(name)
        if attr is None:
            attr = self.add_child(name, Attribute(name, parent=self))
        return attr

    def __execute(self, cmd_name, *args, **kwargs):
        result = self.command_inout(cmd_name, *args, **kwargs)
        return result

    def execute(self, cmd_name, *args, **kwargs):
        return task(self.__execute, cmd_name, *args, **kwargs)        

    def __getattr__(self, name):
        return getattr(self.hw_device, name)


def on_change_event(attr_ref, event_data):
    attr = attr_ref()
    if attr is not None:
        task(attr._on_change_event_task_safe, event_data)


def on_config_event(attr_ref, event_data):
    attr = attr_ref()
    if attr is not None:
        task(attr._on_config_event_task_safe, event_data)


def init_attribute(attr_ref):
    attr = attr_ref()
    if attr is not None:
        attr._init_safe()


class Attribute(_Attribute):

    def __init__(self, name, parent=None):
        _Attribute.__init__(self, name, parent=parent)
        self.__attr_value = None
        self.__attr_config = None
        self.__event_ids = set()
        task(init_attribute, weakref.ref(self))

    def __del__(self):
        self.clean_up()

    @log.debug_it
    def clean_up(self):
        evts = self.__event_ids
        dev = self.device.hw_device
        while True:
            try:
                evt = evts.pop()
            except KeyError:
                break
            try:
                dev.unsubscribe_event(evt)
            except:
                log.error("Failed to unsubscribe from event %d", evt)

    def _init_safe(self):
        try:
            return self.__init()
        except:
            log.error("Exception in Attribute(%s).__init", self.name,
                      exc_info='debug')

    def __init(self):
        dev = self.device.hw_device
        evt_type = Tango.EventType.ATTR_CONF_EVENT
        cb = functools.partial(on_config_event, weakref.ref(self))
        try:
            evt_id = dev.subscribe_event(self.name, evt_type, cb)
        except Tango.DevFailed:
            evt_id = dev.subscribe_event(self.name, evt_type, cb, [], True)
        self.__event_ids.add(evt_id)
        
        evt_type = Tango.EventType.CHANGE_EVENT
        cb = functools.partial(on_change_event, weakref.ref(self))
        try:
            evt_id = dev.subscribe_event(self.name, evt_type, cb)
        except Tango.DevFailed:
            evt_id = dev.subscribe_event(self.name, evt_type, cb, [], True)
        self.__event_ids.add(evt_id)

    @log.debug_it
    def _on_change_event_task_safe(self, event_data):
        try:
            self.__on_change_event_task(event_data)
        except:
            log.error("Exception in change event callback", exc_info='debug')

    @log.debug_it
    def __on_change_event_task(self, event_data):
        if event_data.err:
            errors = event_data.errors
            if len(errors):
                reason = errors[0].reason
                if reason in EVENT_TO_POLLING_EXCEPTIONS:
                    # TODO: start polling
                    pass
                else:
                    attr_value = AttributeValue(Tango.DevFailed(*errors))
                    self.__attr_value = attr_value
                    self.errorOccurred.emit(attr_value)
        else:
            attr_config = self.__get_config()
            attr_value = attr_value_t2q(attr_config, event_data.attr_value)
            self.__attr_value = attr_value
            self.valueChanged.emit(attr_value)

    @log.debug_it
    def _on_config_event_task_safe(self, attr_cfg_event):
        try:
            self.__on_config_event_task(attr_cfg_event)
        except:
            log.error("Exception in config event callback", exc_info='debug')

    @log.debug_it
    def __on_config_event_task(self, attr_cfg_event):
        self.__attr_config = cfg = attr_config_t2q(attr_cfg_event.attr_conf)
        value = self.__attr_value
        if value is None:
            value = self.read()
        else:
            try:
                self._attr_value = value = clone_attr_value(cfg, value)
            except:
                import traceback; traceback.print_exc()
        self.valueChanged.emit(value)

    def __get_config(self):
        cfg = self.__attr_config
        if cfg is None:
            hw = self.device.hw_device
            attr_cfg_f = task(hw.get_attribute_config, self.name)
            cfg = TangoAttributeConfigFuture(attr_cfg_f)
            self.__attr_config = cfg
        return cfg

    def __get_value(self):
        value = self.__attr_value
        if value is None:
            value = self.__read()
        return value

    def __read(self):
        hw = self.device.hw_device
        dev_attr_f = task(hw.read_attribute, self.name)
        attr_config = self.__get_config()
        attr_value = TangoAttributeValueFuture(dev_attr_f, attr_config)
        self.__attr_value = attr_value
        return attr_value

    # -- API ------------------------------------------------------------------

    def read(self):
        return self.__read()

    def write(self):
        pass

    def get_value(self):
        return self.__get_value()


class TangoFactory(_Factory):

    def __init__(self):
        _Factory.__init__(self)

    @log.debug_it
    def get_database(self, name=None):
        if name is None:
            name = Tango.ApiUtil.get_env_var("TANGO_HOST")
            if name is None:
                raise KeyError("Default tango database not defined")
        name = name.lower()
        database = self.get_child(name)
        if database is None:
            database = self.add_child(name, Database(name))         
        return database

    @log.debug_it
    def get_device(self, name):
        #TODO: slit name into database and device
        database = self.get_database()
        return database.get_device(name)

    @log.debug_it
    def get_attribute(self, name):
        #TODO: split properly
        dev_name, name = name.rsplit("/", 1)
        device = self.get_device(dev_name)
        return device.get_attribute(name)       


__factory = None
def Factory():
    global __factory
    if __factory is None:
        __factory = TangoFactory()
    return __factory


def main():
    import sys
    import time
    from qarbon import config
    
    config.EXECUTOR = "thread"
    config.MAX_WORKERS = 1
    
    log.initialize(log_level='debug')
    
    attr_name = 'sys/tg_test/1/double_scalar'
    if len(sys.argv) > 1:
        attr_name = sys.argv[1]

    f = Factory()
    attr = f.get_attribute(attr_name)

    @log.info_it
    def value_changed(new_value):
        log.debug("event value: %s", new_value)
    attr.valueChanged.connect(value_changed)

    v = attr.read()
    log.info("Read value: %s", v)

    count = 0
    try:
        while True:
            time.sleep(1)
            count += 1
            if count == 3:
                log.warning("delete attr")
                del value_changed
                del attr
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

