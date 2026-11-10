from phoenix.cli import check_fixture, main


def test_cli_check_success():
    exit_code = check_fixture("benchmarks/fixtures/shop_a")
    assert exit_code == 0


def test_cli_check_missing_spec(tmp_path):
    exit_code = check_fixture(tmp_path)
    assert exit_code == 1


def test_cli_main_check():
    assert main(["check", "benchmarks/fixtures/shop_a"]) == 0


def test_cli_main_help():
    assert main([]) == 0
