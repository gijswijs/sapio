#!/usr/bin/env python3
# Copyright (c) 2015-2019 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Functionality to build scripts, as well as signature hash functions.

This file is modified from python-sapio_bitcoinlib.
"""
from __future__ import annotations

import hashlib
import struct
from typing import (
    Dict,
    List,
    AnyStr,
    Union,
    Type,
    Iterator,
    Tuple,
    Any,
    Optional,
    Iterable,
)

from .static_types import min_int64, max_int64, uint32, int64

from .hash_functions import sha256, AnyBytes
from .bignum import bn2vch

MAX_SCRIPT_ELEMENT_SIZE = 520

OPCODE_NAMES: Dict[CScriptOp, str] = {}


def hash160(s: AnyBytes) -> bytes:
    return hashlib.new("ripemd160", sha256(s)).digest()


_opcode_instances: List[CScriptOp] = []


class CScriptOp(int):
    """A single script opcode"""

    __slots__ = ()

    @staticmethod
    def encode_op_pushdata(d: bytes) -> bytes:
        """Encode a PUSHDATA op, returning bytes"""
        if len(d) < 0x4C:
            return b"" + bytes([len(d)]) + d  # OP_PUSHDATA
        elif len(d) <= 0xFF:
            return b"\x4c" + bytes([len(d)]) + d  # OP_PUSHDATA1
        elif len(d) <= 0xFFFF:
            return b"\x4d" + struct.pack(b"<H", len(d)) + d  # OP_PUSHDATA2
        elif len(d) <= 0xFFFFFFFF:
            return b"\x4e" + struct.pack(b"<I", len(d)) + d  # OP_PUSHDATA4
        else:
            raise ValueError("Data too long to encode in a PUSHDATA op")

    @staticmethod
    def encode_op_n(n: int) -> CScriptOp:
        """Encode a small integer op, returning an opcode"""
        if not (0 <= n <= 16):
            raise ValueError("Integer must be in range 0 <= n <= 16, got %d" % n)

        if n == 0:
            return OP_0
        else:
            return CScriptOp(OP_1 + n - 1)

    def decode_op_n(self) -> int:
        """Decode a small integer opcode, returning an integer"""
        if self == OP_0:
            return 0

        if not (self == OP_0 or OP_1 <= self <= OP_16):
            raise ValueError("op %r is not an OP_N" % self)

        return int(self - OP_1 + 1)

    def is_small_int(self) -> bool:
        """Return true if the op pushes a small integer to the stack"""
        if 0x51 <= self <= 0x60 or self == 0:
            return True
        else:
            return False

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        if self in OPCODE_NAMES:
            return OPCODE_NAMES[self]
        else:
            return "CScriptOp(0x%x)" % self

    def __new__(cls, n: int) -> CScriptOp:
        try:
            return _opcode_instances[n]
        except IndexError:
            assert len(_opcode_instances) == n
            _opcode_instances.append(super(CScriptOp, cls).__new__(cls, n))
            return _opcode_instances[n]


# Populate opcode instance table
for n in range(0xFF + 1):
    CScriptOp(n)


# push value
OP_0 = CScriptOp(0x00)
OP_FALSE = OP_0
OP_PUSHDATA1 = CScriptOp(0x4C)
OP_PUSHDATA2 = CScriptOp(0x4D)
OP_PUSHDATA4 = CScriptOp(0x4E)
OP_1NEGATE = CScriptOp(0x4F)
OP_RESERVED = CScriptOp(0x50)
OP_1 = CScriptOp(0x51)
OP_TRUE = OP_1
OP_2 = CScriptOp(0x52)
OP_3 = CScriptOp(0x53)
OP_4 = CScriptOp(0x54)
OP_5 = CScriptOp(0x55)
OP_6 = CScriptOp(0x56)
OP_7 = CScriptOp(0x57)
OP_8 = CScriptOp(0x58)
OP_9 = CScriptOp(0x59)
OP_10 = CScriptOp(0x5A)
OP_11 = CScriptOp(0x5B)
OP_12 = CScriptOp(0x5C)
OP_13 = CScriptOp(0x5D)
OP_14 = CScriptOp(0x5E)
OP_15 = CScriptOp(0x5F)
OP_16 = CScriptOp(0x60)

# control
OP_NOP = CScriptOp(0x61)
OP_VER = CScriptOp(0x62)
OP_IF = CScriptOp(0x63)
OP_NOTIF = CScriptOp(0x64)
OP_VERIF = CScriptOp(0x65)
OP_VERNOTIF = CScriptOp(0x66)
OP_ELSE = CScriptOp(0x67)
OP_ENDIF = CScriptOp(0x68)
OP_VERIFY = CScriptOp(0x69)
OP_RETURN = CScriptOp(0x6A)

# stack ops
OP_TOALTSTACK = CScriptOp(0x6B)
OP_FROMALTSTACK = CScriptOp(0x6C)
OP_2DROP = CScriptOp(0x6D)
OP_2DUP = CScriptOp(0x6E)
OP_3DUP = CScriptOp(0x6F)
OP_2OVER = CScriptOp(0x70)
OP_2ROT = CScriptOp(0x71)
OP_2SWAP = CScriptOp(0x72)
OP_IFDUP = CScriptOp(0x73)
OP_DEPTH = CScriptOp(0x74)
OP_DROP = CScriptOp(0x75)
OP_DUP = CScriptOp(0x76)
OP_NIP = CScriptOp(0x77)
OP_OVER = CScriptOp(0x78)
OP_PICK = CScriptOp(0x79)
OP_ROLL = CScriptOp(0x7A)
OP_ROT = CScriptOp(0x7B)
OP_SWAP = CScriptOp(0x7C)
OP_TUCK = CScriptOp(0x7D)

# splice ops
OP_CAT = CScriptOp(0x7E)
OP_SUBSTR = CScriptOp(0x7F)
OP_LEFT = CScriptOp(0x80)
OP_RIGHT = CScriptOp(0x81)
OP_SIZE = CScriptOp(0x82)

# bit logic
OP_INVERT = CScriptOp(0x83)
OP_AND = CScriptOp(0x84)
OP_OR = CScriptOp(0x85)
OP_XOR = CScriptOp(0x86)
OP_EQUAL = CScriptOp(0x87)
OP_EQUALVERIFY = CScriptOp(0x88)
OP_RESERVED1 = CScriptOp(0x89)
OP_RESERVED2 = CScriptOp(0x8A)

# numeric
OP_1ADD = CScriptOp(0x8B)
OP_1SUB = CScriptOp(0x8C)
OP_2MUL = CScriptOp(0x8D)
OP_2DIV = CScriptOp(0x8E)
OP_NEGATE = CScriptOp(0x8F)
OP_ABS = CScriptOp(0x90)
OP_NOT = CScriptOp(0x91)
OP_0NOTEQUAL = CScriptOp(0x92)

OP_ADD = CScriptOp(0x93)
OP_SUB = CScriptOp(0x94)
OP_MUL = CScriptOp(0x95)
OP_DIV = CScriptOp(0x96)
OP_MOD = CScriptOp(0x97)
OP_LSHIFT = CScriptOp(0x98)
OP_RSHIFT = CScriptOp(0x99)

OP_BOOLAND = CScriptOp(0x9A)
OP_BOOLOR = CScriptOp(0x9B)
OP_NUMEQUAL = CScriptOp(0x9C)
OP_NUMEQUALVERIFY = CScriptOp(0x9D)
OP_NUMNOTEQUAL = CScriptOp(0x9E)
OP_LESSTHAN = CScriptOp(0x9F)
OP_GREATERTHAN = CScriptOp(0xA0)
OP_LESSTHANOREQUAL = CScriptOp(0xA1)
OP_GREATERTHANOREQUAL = CScriptOp(0xA2)
OP_MIN = CScriptOp(0xA3)
OP_MAX = CScriptOp(0xA4)

OP_WITHIN = CScriptOp(0xA5)

# crypto
OP_RIPEMD160 = CScriptOp(0xA6)
OP_SHA1 = CScriptOp(0xA7)
OP_SHA256 = CScriptOp(0xA8)
OP_HASH160 = CScriptOp(0xA9)
OP_HASH256 = CScriptOp(0xAA)
OP_CODESEPARATOR = CScriptOp(0xAB)
OP_CHECKSIG = CScriptOp(0xAC)
OP_CHECKSIGVERIFY = CScriptOp(0xAD)
OP_CHECKMULTISIG = CScriptOp(0xAE)
OP_CHECKMULTISIGVERIFY = CScriptOp(0xAF)

# expansion
OP_NOP1 = CScriptOp(0xB0)
OP_CHECKLOCKTIMEVERIFY = CScriptOp(0xB1)
OP_CHECKSEQUENCEVERIFY = CScriptOp(0xB2)
OP_CHECKTEMPLATEVERIFY = CScriptOp(0xB3)
OP_NOP5 = CScriptOp(0xB4)
OP_NOP6 = CScriptOp(0xB5)
OP_NOP7 = CScriptOp(0xB6)
OP_NOP8 = CScriptOp(0xB7)
OP_NOP9 = CScriptOp(0xB8)
OP_NOP10 = CScriptOp(0xB9)

# template matching params
OP_SMALLINTEGER = CScriptOp(0xFA)
OP_PUBKEYS = CScriptOp(0xFB)
OP_PUBKEYHASH = CScriptOp(0xFD)
OP_PUBKEY = CScriptOp(0xFE)

OP_INVALIDOPCODE = CScriptOp(0xFF)

OPCODE_NAMES.update(
    {
        OP_0: "OP_0",
        OP_PUSHDATA1: "OP_PUSHDATA1",
        OP_PUSHDATA2: "OP_PUSHDATA2",
        OP_PUSHDATA4: "OP_PUSHDATA4",
        OP_1NEGATE: "OP_1NEGATE",
        OP_RESERVED: "OP_RESERVED",
        OP_1: "OP_1",
        OP_2: "OP_2",
        OP_3: "OP_3",
        OP_4: "OP_4",
        OP_5: "OP_5",
        OP_6: "OP_6",
        OP_7: "OP_7",
        OP_8: "OP_8",
        OP_9: "OP_9",
        OP_10: "OP_10",
        OP_11: "OP_11",
        OP_12: "OP_12",
        OP_13: "OP_13",
        OP_14: "OP_14",
        OP_15: "OP_15",
        OP_16: "OP_16",
        OP_NOP: "OP_NOP",
        OP_VER: "OP_VER",
        OP_IF: "OP_IF",
        OP_NOTIF: "OP_NOTIF",
        OP_VERIF: "OP_VERIF",
        OP_VERNOTIF: "OP_VERNOTIF",
        OP_ELSE: "OP_ELSE",
        OP_ENDIF: "OP_ENDIF",
        OP_VERIFY: "OP_VERIFY",
        OP_RETURN: "OP_RETURN",
        OP_TOALTSTACK: "OP_TOALTSTACK",
        OP_FROMALTSTACK: "OP_FROMALTSTACK",
        OP_2DROP: "OP_2DROP",
        OP_2DUP: "OP_2DUP",
        OP_3DUP: "OP_3DUP",
        OP_2OVER: "OP_2OVER",
        OP_2ROT: "OP_2ROT",
        OP_2SWAP: "OP_2SWAP",
        OP_IFDUP: "OP_IFDUP",
        OP_DEPTH: "OP_DEPTH",
        OP_DROP: "OP_DROP",
        OP_DUP: "OP_DUP",
        OP_NIP: "OP_NIP",
        OP_OVER: "OP_OVER",
        OP_PICK: "OP_PICK",
        OP_ROLL: "OP_ROLL",
        OP_ROT: "OP_ROT",
        OP_SWAP: "OP_SWAP",
        OP_TUCK: "OP_TUCK",
        OP_CAT: "OP_CAT",
        OP_SUBSTR: "OP_SUBSTR",
        OP_LEFT: "OP_LEFT",
        OP_RIGHT: "OP_RIGHT",
        OP_SIZE: "OP_SIZE",
        OP_INVERT: "OP_INVERT",
        OP_AND: "OP_AND",
        OP_OR: "OP_OR",
        OP_XOR: "OP_XOR",
        OP_EQUAL: "OP_EQUAL",
        OP_EQUALVERIFY: "OP_EQUALVERIFY",
        OP_RESERVED1: "OP_RESERVED1",
        OP_RESERVED2: "OP_RESERVED2",
        OP_1ADD: "OP_1ADD",
        OP_1SUB: "OP_1SUB",
        OP_2MUL: "OP_2MUL",
        OP_2DIV: "OP_2DIV",
        OP_NEGATE: "OP_NEGATE",
        OP_ABS: "OP_ABS",
        OP_NOT: "OP_NOT",
        OP_0NOTEQUAL: "OP_0NOTEQUAL",
        OP_ADD: "OP_ADD",
        OP_SUB: "OP_SUB",
        OP_MUL: "OP_MUL",
        OP_DIV: "OP_DIV",
        OP_MOD: "OP_MOD",
        OP_LSHIFT: "OP_LSHIFT",
        OP_RSHIFT: "OP_RSHIFT",
        OP_BOOLAND: "OP_BOOLAND",
        OP_BOOLOR: "OP_BOOLOR",
        OP_NUMEQUAL: "OP_NUMEQUAL",
        OP_NUMEQUALVERIFY: "OP_NUMEQUALVERIFY",
        OP_NUMNOTEQUAL: "OP_NUMNOTEQUAL",
        OP_LESSTHAN: "OP_LESSTHAN",
        OP_GREATERTHAN: "OP_GREATERTHAN",
        OP_LESSTHANOREQUAL: "OP_LESSTHANOREQUAL",
        OP_GREATERTHANOREQUAL: "OP_GREATERTHANOREQUAL",
        OP_MIN: "OP_MIN",
        OP_MAX: "OP_MAX",
        OP_WITHIN: "OP_WITHIN",
        OP_RIPEMD160: "OP_RIPEMD160",
        OP_SHA1: "OP_SHA1",
        OP_SHA256: "OP_SHA256",
        OP_HASH160: "OP_HASH160",
        OP_HASH256: "OP_HASH256",
        OP_CODESEPARATOR: "OP_CODESEPARATOR",
        OP_CHECKSIG: "OP_CHECKSIG",
        OP_CHECKSIGVERIFY: "OP_CHECKSIGVERIFY",
        OP_CHECKMULTISIG: "OP_CHECKMULTISIG",
        OP_CHECKMULTISIGVERIFY: "OP_CHECKMULTISIGVERIFY",
        OP_NOP1: "OP_NOP1",
        OP_CHECKLOCKTIMEVERIFY: "OP_CHECKLOCKTIMEVERIFY",
        OP_CHECKSEQUENCEVERIFY: "OP_CHECKSEQUENCEVERIFY",
        OP_CHECKTEMPLATEVERIFY: "OP_CHECKTEMPLATEVERIFY",
        OP_NOP5: "OP_NOP5",
        OP_NOP6: "OP_NOP6",
        OP_NOP7: "OP_NOP7",
        OP_NOP8: "OP_NOP8",
        OP_NOP9: "OP_NOP9",
        OP_NOP10: "OP_NOP10",
        OP_SMALLINTEGER: "OP_SMALLINTEGER",
        OP_PUBKEYS: "OP_PUBKEYS",
        OP_PUBKEYHASH: "OP_PUBKEYHASH",
        OP_PUBKEY: "OP_PUBKEY",
        OP_INVALIDOPCODE: "OP_INVALIDOPCODE",
    }
)


class CScriptInvalidError(Exception):
    """Base class for CScript exceptions"""

    pass


class CScriptTruncatedPushDataError(CScriptInvalidError):
    """Invalid pushdata due to truncation"""

    def __init__(self, msg: str, data: bytes) -> None:
        self.data = data
        super(CScriptTruncatedPushDataError, self).__init__(msg)


# This is used, eg, for blockchain heights in coinbase scripts (bip34)
class CScriptNum:
    __slots__ = ("value",)

    def __init__(self, d: int = 0):
        self.value = d

    @staticmethod
    def encode(obj: CScriptNum) -> bytes:
        r = bytearray(0)
        if obj.value == 0:
            return bytes(r)
        neg = obj.value < 0
        absvalue = -obj.value if neg else obj.value
        while absvalue:
            r.append(absvalue & 0xFF)
            absvalue >>= 8
        if r[-1] & 0x80:
            r.append(0x80 if neg else 0)
        elif neg:
            r[-1] |= 0x80
        return bytes([len(r)]) + r

    @staticmethod
    def decode(vch: bytes) -> int:
        result = 0
        # We assume valid push_size and minimal encoding
        value = vch[1:]
        if len(value) == 0:
            return result
        for i, byte in enumerate(value):
            result |= int(byte) << 8 * i
        if value[-1] >= 0x80:
            # Mask for all but the highest result bit
            num_mask = (2 ** (len(value) * 8) - 1) >> 1
            result &= num_mask
            result *= -1
        return result

    def __sub__(self, other: CScriptNum) -> CScriptNum:
        rhs = other.value
        assert (
            rhs == 0
            or (rhs > 0 and self.value >= (min_int64 + rhs))
            or (rhs < 0 and self.value <= (max_int64 + rhs))
        )
        return CScriptNum(self.value - rhs)


class CScript(bytes):
    """Serialized script

    A bytes subclass, so you can use this directly whenever bytes are accepted.
    Note that this means that indexing does *not* work - you'll get an index by
    byte rather than opcode. This format was chosen for efficiency so that the
    general case would not require creating a lot of little CScriptOP objects.

    iter(script) however does iterate by opcode.
    """

    __slots__ = ()
    Coercable = Union[CScriptOp, CScriptNum, int, "CScript", bytes, bytearray]

    @classmethod
    def __coerce_instance(cls, other: Coercable) -> bytes:
        # Coerce other into bytes
        if isinstance(other, CScriptOp):
            other = bytes([other])
        elif isinstance(other, CScriptNum):
            if other.value == 0:
                other = bytes([CScriptOp(OP_0)])
            else:
                other = CScriptNum.encode(other)
        elif isinstance(other, (int, uint32, int64)):
            # corerce to python int
            other = int(other)
            if 0 <= other <= 16:
                other = bytes([CScriptOp.encode_op_n(other)])
            elif other == -1:
                other = bytes([OP_1NEGATE])
            else:
                other = CScriptOp.encode_op_pushdata(bn2vch(other))
        elif isinstance(other, CScript):
            pass
        elif isinstance(other, (bytes, bytearray)):
            other = CScriptOp.encode_op_pushdata(other)
        else:
            raise ValueError("Type cannot coerce", other, type(other))
        return other

    def __add__(self, other: Coercable) -> CScript:
        # Do the coercion outside of the try block so that errors in it are
        # noticed.
        other = self.__coerce_instance(other)

        try:
            # bytes.__add__ always returns bytes instances unfortunately
            return CScript(super(CScript, self).__add__(other))
        except TypeError:
            raise TypeError("Can not add a %r instance to a CScript" % other.__class__)

    def join(self, iterable: Any) -> bytes:
        # join makes no sense for a CScript()
        raise NotImplementedError

    def __new__(
        cls, value: Union[Iterable[Coercable], bytes, bytearray] = b""
    ) -> CScript:
        if isinstance(value, bytes) or isinstance(value, bytearray):
            c: CScript = super(CScript, cls).__new__(cls, value)
            return c
        else:

            def coerce_iterable(
                iterable: Iterable[CScript.Coercable],
            ) -> Iterator[bytes]:
                for instance in iterable:
                    yield cls.__coerce_instance(instance)

            # Annoyingly on both python2 and python3 bytes.join() always
            # returns a bytes instance even when subclassed.
            c = super(CScript, cls).__new__(cls, b"".join(coerce_iterable(value)))
            return c

    def raw_iter(self) -> Iterator[Tuple[CScriptOp, Optional[bytes], int]]:
        """Raw iteration

        Yields tuples of (opcode, data, sop_idx) so that the different possible
        PUSHDATA encodings can be accurately distinguished, as well as
        determining the exact opcode byte indexes. (sop_idx)
        """
        i = 0
        while i < len(self):
            sop_idx = i
            opcode = self[i]
            i += 1

            if opcode > OP_PUSHDATA4:
                yield (CScriptOp(opcode), None, sop_idx)
            else:
                datasize = None
                pushdata_type = None
                if opcode < OP_PUSHDATA1:
                    pushdata_type = "PUSHDATA(%d)" % opcode
                    datasize = opcode

                elif opcode == OP_PUSHDATA1:
                    pushdata_type = "PUSHDATA1"
                    if i >= len(self):
                        raise CScriptInvalidError("PUSHDATA1: missing data length")
                    datasize = self[i]
                    i += 1

                elif opcode == OP_PUSHDATA2:
                    pushdata_type = "PUSHDATA2"
                    if i + 1 >= len(self):
                        raise CScriptInvalidError("PUSHDATA2: missing data length")
                    datasize = self[i] + (self[i + 1] << 8)
                    i += 2

                elif opcode == OP_PUSHDATA4:
                    pushdata_type = "PUSHDATA4"
                    if i + 3 >= len(self):
                        raise CScriptInvalidError("PUSHDATA4: missing data length")
                    datasize = (
                        self[i]
                        + (self[i + 1] << 8)
                        + (self[i + 2] << 16)
                        + (self[i + 3] << 24)
                    )
                    i += 4

                else:
                    assert False  # shouldn't happen

                data = bytes(self[i : i + datasize])

                # Check for truncation
                if len(data) < datasize:
                    raise CScriptTruncatedPushDataError(
                        "%s: truncated data" % pushdata_type, data
                    )

                i += datasize

                yield (CScriptOp(opcode), data, sop_idx)

    # TODO: Fix the typing here because this violates Liskov substitution
    def __iter__(self) -> Iterator[Any]:
        """'Cooked' iteration

        Returns either a CScriptOP instance, an integer, or bytes, as
        appropriate.

        See raw_iter() if you need to distinguish the different possible
        PUSHDATA encodings.
        """
        for (opcode, data, sop_idx) in self.raw_iter():
            if data is not None:
                yield data
            else:
                opcode = CScriptOp(opcode)

                if opcode.is_small_int():
                    yield opcode.decode_op_n()
                else:
                    yield opcode

    def __repr__(self) -> str:
        def _repr(o: Any) -> str:
            if isinstance(o, bytes):
                return "x('%s')" % o.hex()
            else:
                return repr(o)

        ops = []
        i = iter(self)
        while True:
            op = None
            try:
                op = _repr(next(i))
            except CScriptTruncatedPushDataError as err:
                op = "%s...<ERROR: %s>" % (_repr(err.data), err)
                break
            except CScriptInvalidError as err:
                op = "<ERROR: %s>" % err
                break
            except StopIteration:
                break
            finally:
                if op is not None:
                    ops.append(op)

        return "CScript([%s])" % ", ".join(ops)

    def GetSigOpCount(self, fAccurate: bool) -> int:
        """Get the SigOp count.

        fAccurate - Accurately count CHECKMULTISIG, see BIP16 for details.

        Note that this is consensus-critical.
        """
        n = 0
        lastOpcode = OP_INVALIDOPCODE
        for (opcode, data, sop_idx) in self.raw_iter():
            if opcode in (OP_CHECKSIG, OP_CHECKSIGVERIFY):
                n += 1
            elif opcode in (OP_CHECKMULTISIG, OP_CHECKMULTISIGVERIFY):
                if fAccurate and (OP_1 <= lastOpcode <= OP_16):
                    n += opcode.decode_op_n()
                else:
                    n += 20
            lastOpcode = opcode
        return n


SIGHASH_ALL = 1
SIGHASH_NONE = 2
SIGHASH_SINGLE = 3
SIGHASH_ANYONECANPAY = 0x80


def FindAndDelete(script: CScript, sig: bytes) -> CScript:
    """Consensus critical, see FindAndDelete() in Satoshi codebase"""
    r = b""
    last_sop_idx = sop_idx = 0
    skip = True
    for (opcode, data, sop_idx) in script.raw_iter():
        if not skip:
            r += script[last_sop_idx:sop_idx]
        last_sop_idx = sop_idx
        if script[sop_idx : sop_idx + len(sig)] == sig:
            skip = True
        else:
            skip = False
    if not skip:
        r += script[last_sop_idx:]
    return CScript(r)
