import unittest

from coco.b09.procbank import ProcedureBank, parse_param_line


class TestProcedureBank(unittest.TestCase):
    def test_includes_given_procedure(self) -> None:
        target = ProcedureBank()
        assert {"foo"} == target._get_procedure_and_dependency_names("foo")

    def test_loads_procedures_from_str(self) -> None:
        target = ProcedureBank()
        procedure = (
            "PROCEDURE foo\nRUN bar()\nPROCEDURE bar\nRUN baz()\n"
            'PROCEDURE baz\nPRINT "HELLO"'
        )
        target.add_from_str(procedure)
        assert {"foo", "bar", "baz"} == target._get_procedure_and_dependency_names(
            "foo"
        )

    def test_loads_procedures_from_resource(self) -> None:
        target = ProcedureBank()
        target.add_from_resource("ecb.b09")
        assert {"ecb_point", "_ecb_get_point_info", "_ecb_text_address"}.issubset(
            target._get_procedure_and_dependency_names("ecb_point")
        )

    def test_can_load_from_resource_and_str(self) -> None:
        target = ProcedureBank()
        target.add_from_resource("ecb.b09")
        procedure = "PROCEDURE foo\nRUN ecb_cls(5)\n\n"
        target.add_from_str(procedure)
        assert {"foo", "ecb_cls", "_ecb_text_address"}.issubset(
            target._get_procedure_and_dependency_names("foo")
        )
        all_procedures = target.get_procedure_and_dependencies("foo")
        assert all_procedures.endswith(procedure.strip())
        assert all_procedures.startswith("procedure _ecb_text_address\n")
        assert "procedure ecb_cls\n" in all_procedures

    def test_substitutes_str_storage_tag_with_default(self) -> None:
        target = ProcedureBank()
        target.add_from_resource("ecb.b09")
        procedure = "PROCEDURE foo\nRUN ecb_string()\n\n"
        target.add_from_str(procedure)
        assert (
            "param str: STRING\n(* Out *)\nparam strout: STRING"
            in target.get_procedure_and_dependencies("foo")
        )

    def test_substitutes_str_storage_tag(self) -> None:
        target = ProcedureBank(default_str_storage=80)
        target.add_from_resource("ecb.b09")
        procedure = "PROCEDURE foo\nRUN ecb_string()\n\n"
        target.add_from_str(procedure)
        assert (
            "param str: STRING[80]\n(* Out *)\nparam strout: STRING[80]"
            in target.get_procedure_and_dependencies("foo")
        )


class TestParseParamLine(unittest.TestCase):
    def test_simple_param(self) -> None:
        params = parse_param_line("param v: real")
        assert len(params) == 1
        assert params[0].name == "v"
        assert params[0].type == "real"
        assert not params[0].is_output
        assert params[0].is_real
        assert not params[0].is_integer

    def test_multi_name_param(self) -> None:
        params = parse_param_line("param a, b, c: integer")
        assert [p.name for p in params] == ["a", "b", "c"]
        assert all(p.type == "integer" for p in params)
        assert all(p.is_integer for p in params)
        assert not any(p.is_output for p in params)

    def test_is_output_kwarg_marks_param(self) -> None:
        params = parse_param_line("param retval: real", is_output=True)
        assert params[0].name == "retval"
        assert params[0].is_output

    def test_is_output_kwarg_applies_to_all_names(self) -> None:
        params = parse_param_line(
            "param joy0x, joy0y, joy1x, joy1y, retval: real",
            is_output=True,
        )
        assert len(params) == 5
        assert all(p.is_output for p in params)

    def test_default_is_input(self) -> None:
        params = parse_param_line("param retval: real")
        assert len(params) == 1
        assert not params[0].is_output

    def test_string_type_with_size(self) -> None:
        params = parse_param_line("param txt: string[80]")
        assert params[0].type == "string[80]"

    def test_string_type_with_storage_tag(self) -> None:
        params = parse_param_line("PARAM s: STRING<<>>")
        assert params[0].type == "STRING<<>>"

    def test_non_param_line_returns_empty(self) -> None:
        assert parse_param_line("dim foo: integer") == []


class TestProcedureBankSignatures(unittest.TestCase):
    def test_signature_for_input_only_procedure(self) -> None:
        bank = ProcedureBank()
        bank.add_from_resource("ecb.b09")
        sig = bank.signatures["ecb_at"]
        assert sig.name == "ecb_at"
        assert [p.name for p in sig.params] == ["location"]
        assert not sig.params[0].is_output

    def test_signature_for_single_output_param(self) -> None:
        bank = ProcedureBank()
        bank.add_from_resource("ecb.b09")
        sig = bank.signatures["ecb_int"]
        assert [(p.name, p.is_output) for p in sig.params] == [
            ("v", False),
            ("retval", True),
        ]
        assert sig.params[1].is_real

    def test_signature_with_multiple_output_reals(self) -> None:
        bank = ProcedureBank()
        bank.add_from_resource("ecb.b09")
        sig = bank.signatures["ecb_joystk"]
        outs = [p.name for p in sig.params if p.is_output]
        assert outs == ["joy0x", "joy0y", "joy1x", "joy1y", "retval"]

    def test_signature_with_integer_output(self) -> None:
        bank = ProcedureBank()
        bank.add_from_resource("ecb.b09")
        sig = bank.signatures["_ecb_max"]
        assert sig.params[0].name == "x2"
        assert sig.params[0].is_output
        assert sig.params[0].is_integer
        assert not sig.params[1].is_output
        assert not sig.params[2].is_output

    def test_signatures_cover_all_procedures_in_ecb_b09(self) -> None:
        bank = ProcedureBank()
        bank.add_from_resource("ecb.b09")
        # Every known procedure has a signature entry (even ones
        # with no parameters such as _ecb_input_prefix).
        for name in (
            "ecb_at",
            "ecb_cls",
            "ecb_int",
            "ecb_joystk",
            "_ecb_input_prefix",
            "_ecb_wintype",
        ):
            assert name in bank.signatures

    def test_marker_on_preceding_line_marks_next_param(self) -> None:
        bank = ProcedureBank()
        bank.add_from_str(
            "procedure foo\n"
            "param a: real\n"
            "(* Out *)\n"
            "param b: real\n"
            "param c: real\n"
        )
        sig = bank.signatures["foo"]
        assert [(p.name, p.is_output) for p in sig.params] == [
            ("a", False),
            ("b", True),
            ("c", False),
        ]

    def test_marker_with_blank_line_in_between_still_applies(self) -> None:
        bank = ProcedureBank()
        bank.add_from_str("procedure foo\n" "(* Out *)\n" "\n" "param b: real\n")
        assert bank.signatures["foo"].params[0].is_output

    def test_marker_resets_at_procedure_boundary(self) -> None:
        bank = ProcedureBank()
        bank.add_from_str(
            "procedure foo\n" "(* Out *)\n" "procedure bar\n" "param x: real\n"
        )
        # The dangling marker on ``foo`` must not leak into
        # ``bar``'s first param.
        assert not bank.signatures["bar"].params[0].is_output
