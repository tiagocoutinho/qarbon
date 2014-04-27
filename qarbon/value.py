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

__all__ = ["AttributeConfig", "NullAttributeConfig",
           "Value", "NullValue",
           "AttributeValue", "NullAttributeValue"]


from .core import DisplayLevel, Access


class AttributeConfig(object):
    
    name = ""
    label = "-----"
    description = ""
    ndim = -1
    format = "%s"
    display_level = DisplayLevel._Invalid
    display_format = "!s"
    access = Access._Invalid
    unit = None
    standard_unit = None
    display_unit = None
    min_value = None
    max_value = None
    min_alarm = None
    max_alarm = None
    min_warning = None
    max_warning = None
    value_range = None, None
    alarm_range = None, None
    warning_range = None, None

    def is_write(self):
        return self.access == Access.Write

    def is_readonly(self):
        return self.access == Access.Read

    def is_readwrite(self):
        return self.access == Access.ReadWrite

    def is_scalar(self):
        return self.ndim == 0

    def is_spectrum(self):
        return self.ndim == 1

    def is_mage(self):
        return self.ndim == 2


NullAttributeConfig = AttributeConfig()


class Value(object):
    """A qarbon value. A container for a value read from a qarbon model. It
    contains the following members:
    
    * r_value (Quantity): (aka: value) a Quantity representing the read value
    * r_timestamp (datetime.datetime): the timestamp of reading the value
    * w_value (Quantity): a Quantity representing the write value
    * quality (Quality): the quality related to the read value
    * exc_info (tuple): a 3-tuple equivalent to sys.exc_info() if reading a
                        value resulted in an exception or None otherwise
    * error (bool): tells the read resulted in an error

    Example on how to pretty print 

    """

    r_value = None

    r_timestamp = None
    
    r_ndim = None

    r_quality = None

    w_value = None

    exc_info = None

    def __str__(self):
        if self.error:
            value = ErrorStr
        else:
            value = self.r_value
        return "{0}".format(value)

    def __repr__(self):
        cname = self.__class__.__name__
        if self.error:
            value = ErrorRepr
        else:
            value = self.r_value
        return "{0}({1!r})".format(cname, self.r_value)
    
    def __format__(self, format_spec):
        if self.error:
            v = ErrorStr
        else:
            v = format(self.r_value, format_spec)
        return v

    @property
    def value(self):
        return self.r_value

    @property
    def timestamp(self):
        return self.r_timestamp
    
    @property
    def ndim(self):
        return self.r_ndim

    @property
    def quality(self):
        return self.r_quality

    @property
    def error(self):
        return self.exc_info is not None

    def is_scalar(self):
        return self.ndim == 0

    def is_spectrum(self):
        return self.ndim == 1

    def is_image(self):
        return self.ndim == 2


NullValue = Value()


class AttributeValue(Value):
    """A qarbon value. A container for a value read from a qarbon model. It
    contains the following members:
    
    * r_value (Quantity): (aka: value) a Quantity representing the read value
    * r_timestamp (datetime.datetime): the timestamp of reading the value
    * w_value (Quantity): a Quantity representing the write value
    * quality (Quality): the quality related to the read value
    * exc_info (tuple): a 3-tuple equivalent to sys.exc_info() if reading a
                        value resulted in an exception or None otherwise
    * error (bool): tells the read resulted in an error
    * config (AttributeConfig): config object from which this value was obtained

    Other configuration values can also be accessed:

    * name (str): model name from which the value was obtained 
    * min_value (Quantity): minimum value allowed
    * max_value (Quantity): maximum value allowed
    * min_alarm (Quantity): minimum alarm value trigger
    * max_alarm (Quantity): maximum alarm value trigger
    * min_warning (Quantity): minimum warning value trigger
    * max_warning (Quantity): maximum warning value trigger
    * description (str): a description
    

    Example on how to pretty print 

    """

    config = NullAttributeConfig

    def __getattr__(self, name):
        return getattr(self.config, name)

    def __str__(self):
        if self.error:
            value = ErrorStr
        else:
            value = self.r_value
        return "{0}".format(value)

    def __repr__(self):
        cname = self.__class__.__name__
        if self.error:
            value = ErrorRepr
        else:
            value = self.r_value
        return "{0}({1}, {2!r})".format(cname, self.name, self.r_value)
    
    def __format__(self, format_spec):
        if self.error:
            v = ErrorStr
        else:
            v = format(self.r_value, format_spec)
        return '{obj.label}: {0}'.format(v, obj=self)

    def __pformat__(self):
        return """\
AttributeValue
         name = {0.name}
        label = {0.label}
       access = {0.access}
display_level = {0.display_level}
         unit = {0.unit}
  value_range = {0.value_range}
  alarm_range = {0.alarm_range}
warning_range = {0.warning_range}
         ndim = {0.ndim}
      r_value = {0.r_value}
  r_timestamp = {0.r_timestamp}
    r_quality = {0.r_quality}
      w_value = {0.w_value}
        error = {0.error}
""".format(self)


NullAttributeValue = AttributeValue()
