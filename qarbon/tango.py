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

from weakref import WeakValueDictionary
from functools import partial

import PyTango as Tango

from qarbon import log
from qarbon.external.pint import Quantity
from qarbon.executor import submit
from qarbon.core import Signal
from qarbon.core import Device as _Device
from qarbon.core import Attribute as _Attribute
from qarbon.core import Factory as _Factory
from qarbon.core import Quality, Access, DisplayLevel
from qarbon.core import AttributeConfig, AttributeValue

__NO_STR_VALUE = Tango.constants.AlrmValueNotSpec, Tango.constants.StatusNotSet
Dict = WeakValueDictionary
str_2_obj = Tango.str_2_obj


def quantity_t2q(value, units=None, fmt=None):
    res = Quantity(value, units=units)
    if fmt is not None:
        res.default_format = fmt + res.default_format
    return res


def quantity_str2t(value_str, dtype=None, units=None, fmt=None):
    return quantity_t2q(str_2_obj(value_str, dtype), units=units, fmt=fmt)


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
    result.display_unit = display_unit_t2q(tango_cfg.display_unit, to_quantity=numerical)
    result.standard_unit = standard_unit_t2q(tango_cfg.standard_unit, to_quantity=numerical)

    if numerical:
        Q_ = partial(quantity_str2t_no_error, units=units, dtype=dtype, fmt=disp_fmt)
    else:
        Q_ = partial(str_2_obj, tg_type=dtype)
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
        
    quality = quality_t2q(tango_attr_value.quality)
    value = AttributeValue(r_value=r_value, r_quality=quality,
                           r_timestamp=tango_attr_value.time.todatetime(),
                           w_value=w_value, config=attr_cfg)
    return value


class Device(_Device):

    def __init__(self, name):
        _Device.__init__(self, name)
        self.__device = submit(Tango.DeviceProxy, name)
        self.__attr_value_cache = {}
        self.__attr_config_cache = {}

    @property
    def hw_device(self):
        return self.__device.result()   

    def __read_attribute_value(self, attr_name):
        attr_name = attr_name.lower()
        tango_attr_value = self.hw_device.read_attribute(attr_name)
        try:
            attr_cfg = self.__attr_config_cache[attr_name]
        except KeyError:
            attr_cfg = self.__read_attribute_configuration(attr_name)
        attr_value = attr_value_t2q(attr_cfg, tango_attr_value)
        return attr_value

    def __read_attribute_configuration(self, attr_name):
        attr_name = attr_name.lower()
        tango_cfg = self.hw_device.get_attribute_config_ex(attr_name)[0]
        attr_cfg = attr_config_t2q(tango_cfg)
        return attr_cfg

    def __get_attribute_value(self, attr_name):
        attr_name = attr_name.lower()
        attr_value = self.__attr_value_cache.get(attr_name)
        if attr_value is None:
            attr_value = self.__read_attribute(attr_name)
        self.__attr_value_cache[attr_name] = attr_value
        return attr_value

    def __run_command(self, cmd_name, *args, **kwargs):
        result = self.command_inout(cmd_name, *args, **kwargs)
        return result

    def get_state(self):
        return submit(self.hw_device.state)

    def read_attribute(self, attr_name):
        attr_value = submit(self.__read_attribute_value, attr_name)
        self.__attr_value_cache[attr_name] = attr_value
        return attr_value

    def get_attribute_config(self, attr_name):
        attr_name = attr_name.lower()
        attr_cfg = self.__attr_config_cache.get(attr_name)
        if attr_cfg is None:
            attr_cfg = submit(self.__read_attribute_configuration, attr_name)
        self.__attr_config_cache[attr_name] = attr_cfg
        return attr_cfg

    def get_attribute_value(self, attr_name):
        attr_name = attr_name.lower()
        attr_value = self.__attr_value_cache.get(attr_name)
        if attr_value is None:
            attr_value = self.read_attribute(attr_name)
        self.__attr_value_cache[attr_name] = attr_value
        return attr_value

    def run_command(self, cmd_name, *args, **kwargs):
        return submit(self.__run_command,  cmd_name, *args, **kwargs)        

    def __getattr__(self, name):
        return getattr(self.__device, name)


class Attribute(_Attribute):

    valueChanged = Signal()

    def __init__(self, device, name):
        _Attribute.__init__(self, device, name)
        submit(self.__init)

    def __init(self):
        dev = self.device.hw_device
        cfg = dev.get_attribute_config_ex(self.name)[0]
        self.__config = attr_config_t2q(cfg)

        evt_type = Tango.EventType.ATTR_CONF_EVENT
        try:
            dev.subscribe_event(self.name, evt_type, self.__onConfigEvent)
        except Tango.DevFailed:
            dev.subscribe_event(self.name, evt_type, self.__onConfigEvent, True)

        evt_type = Tango.EventType.CHANGE_EVENT
        try:
            dev.subscribe_event(self.name, evt_type, self.__onChangeEvent)
        except Tango.DevFailed:
            dev.subscribe_event(self.name, evt_type, self.__onChangeEvent, True)
    
    @log.info_it
    def __onChangeEvent(self, event_data):
        attr_cfg = self.device.get_attribute_config(self.name)
        attr_value = attr_value_t2q(attr_cfg.result(), event_data.attr_value)
        self.valueChanged.emit(attr_value)

    @log.info_it
    def __onConfigEvent(self, attr_cfg):
        return        
    
        attr_value = self.device.get_attribute_value(self.name)
        att_value = attr_value_t2q(attr_cfg, attr_value)
        self.valueChanged.emit(attr_value)

    def read(self):
        return self.device.read_attribute(self.name)

    def write(self):
        pass

    def get_value(self):
        return self.device.get_attribute_value(self.name)


class Factory(_Factory):

    def __init__(self):
        _Factory.__init__(self)
        self.__devices = Dict() 
    
    @log.debug_it
    def get_device(self, name):
        name_lower = name.lower()
        device = self.__devices.get(name_lower)
        if device is None:
            device = Device(name)         
            self.__devices[name_lower] = device
        return device

    @log.debug_it
    def get_attribute(self, name):
        dev_name, name = name.rsplit("/", 1)
        device = self.get_device(dev_name)
        return Attribute(device, name)       


def main():
    from qarbon import config
    config.EXECUTOR = "thread"
    config.MAX_WORKERS = 5
    log.initialize(log_level='debug')
    f = Factory()
    state_attr = f.get_attribute('test/1/01/state')
    state = state_attr.read().result()
    print type(state), state, state.timestamp
    print "{0}".format(state)

    import time
    time.sleep(5)

if __name__ == "__main__":
    main()

