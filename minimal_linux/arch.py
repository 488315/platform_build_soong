from device_info import target_cpu_abi, target_arch, target_arch_variant, \
    target_2nd_cpu_abi, target_2nd_arch, target_2nd_arch_variant
from arch_list import Arm, Arm64, X86, X86_64, archVariants, cpuVariants, archFeatures, androidArchFeatureMap

# Constants for common variant
COMMON_VARIANT = "common"

# ArchType class
class ArchType:
    def __init__(self, name, multilib):
        self.name = name
        self.field = self._field_name_for_property(name)
        self.multilib = multilib

    def __str__(self):
        return self.name

    @staticmethod
    def _field_name_for_property(name):
        return ''.join([word.capitalize() for word in name.split('_')])

# Arch class
class Arch:
    def __init__(self, arch_type, arch_variant="", cpu_variant="", abi=None, arch_features=None):
        if abi is None:
            abi = []
        if arch_features is None:
            arch_features = []
        self.arch_type = arch_type
        self.arch_variant = arch_variant
        self.cpu_variant = cpu_variant
        self.abi = abi
        self.arch_features = arch_features

    def __str__(self):
        s = str(self.arch_type.name)  # Ensure we are printing the name of ArchType, not the object reference
        if self.arch_variant:
            s += "_" + self.arch_variant
        if self.cpu_variant:
            s += "_" + self.cpu_variant
        return s

# OsType class
class OsType:
    def __init__(self, name, os_class, default_disabled=False, arch_types=None):
        if arch_types is None:
            arch_types = []
        self.name = name
        self.field = self._field_name_for_property(name)
        self.os_class = os_class
        self.default_disabled = default_disabled
        self.arch_types = arch_types

    def __str__(self):
        return self.name

    @staticmethod
    def _field_name_for_property(name):
        return ''.join([word.capitalize() for word in name.split('_')])

    def linux(self):
        return self.name in ["linux_glibc", "linux_musl"]

# OsClass enum
class OsClass:
    GENERIC = "generic"
    DEVICE = "device"
    HOST = "host"

# Create OsTypes
Linux = OsType("linux_glibc", OsClass.HOST, False, [X86, X86_64])
LinuxMusl = OsType("linux_musl", OsClass.HOST, False, [X86, X86_64, Arm64, Arm])
Darwin = OsType("darwin", OsClass.HOST, False, [Arm64, X86_64])
Windows = OsType("windows", OsClass.HOST, True, [X86, X86_64])
CommonOS = OsType("common_os", OsClass.GENERIC, False)

# Target class
class Target:
    def __init__(self, os, arch, native_bridge=False, native_bridge_host_arch_name="", native_bridge_relative_path="", host_cross=False):
        self.os = os
        self.arch = arch
        self.native_bridge = native_bridge
        self.native_bridge_host_arch_name = native_bridge_host_arch_name
        self.native_bridge_relative_path = native_bridge_relative_path
        self.host_cross = host_cross

    def __str__(self):
        return f"{self.os_variation()}_{self.arch_variation()}"

    def os_variation(self):
        return str(self.os)

    def arch_variation(self):
        variation = "native_bridge_" if self.native_bridge else ""
        variation += str(self.arch)
        return variation

# ArchVariantContext class
class ArchVariantContext:
    def module_error(self, fmt, *args):
        print(fmt % args)

    def property_error(self, property, fmt, *args):
        print(f"{property}: {fmt % args}")

# decode_arch function
def decode_arch(os, arch, arch_variant, cpu_variant, abi):
    arch_type = globals().get(arch.capitalize())
    if not arch_type:
        raise ValueError(f"Unknown arch: {arch}")

    arch_obj = Arch(arch_type, arch_variant or "", cpu_variant or "", abi)

    if arch_variant in [arch, "generic"]:
        arch_obj.arch_variant = ""
    if cpu_variant in [arch, "generic"]:
        arch_obj.cpu_variant = ""

    return arch_obj

# Test example using values from device_info
if __name__ == "__main__":
    primary_arch = decode_arch(Linux, target_arch, target_arch_variant, target_cpu_abi, [target_cpu_abi])
    secondary_arch = decode_arch(Linux, target_2nd_arch, target_2nd_arch_variant, target_2nd_cpu_abi, [target_2nd_cpu_abi])
    print(primary_arch)  # Output: x86_64_x86_64_x86_64
    print(secondary_arch)  # Output: x86_x86_x86_64
