import pytest
import os
import io
from PIL import Image
from value_enhancer.models import TargetType, SecretSeverity
from value_enhancer.modules.phone import PhoneHunter
from value_enhancer.modules.secrets import SecretHunter, calculate_shannon_entropy
from value_enhancer.modules.domain import DomainHunter
from value_enhancer.modules.metadata import MetadataHunter
from value_enhancer.orchestrator import ReconOrchestrator


def test_shannon_entropy():
    # Low entropy (uniform string)
    assert calculate_shannon_entropy("aaaaaaaaaa") == 0.0
    # High entropy (random base64/hash)
    high_entropy = calculate_shannon_entropy("x8K9pQ2mZ7vL1wT0rY5bN4cX")
    assert high_entropy > 3.8


def test_secret_hunter():
    hunter = SecretHunter()
    fake_code = """
    # Configuration
    AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
    GITHUB_PAT = "ghp_1234567890abcdefghijklmnopqrstuvwxyzAB"
    NORMAL_VAR = "hello_world"
    """
    findings = hunter.scan_text(fake_code, source_label="test_file.py")
    rule_ids = {f.rule_id for f in findings}

    assert "AWS_KEY" in rule_ids
    assert "GITHUB_PAT" in rule_ids
    assert len(findings) == 2


def test_phone_hunter():
    hunter = PhoneHunter()
    # Test Alberta Calgary number
    res = hunter.scan("403-268-2489")
    assert res.valid is True
    assert res.country_code == 1
    assert res.e164 == "+14032682489"
    assert "Calgary" in (res.location or "")
    assert "America/Edmonton" in (res.timezone or "")
    assert len(res.google_dorks) > 0


def test_metadata_hunter_clean_image(tmp_path):
    hunter = MetadataHunter()
    # Generate a clean image without EXIF
    img_path = str(tmp_path / "test.jpg")
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(img_path)

    res = hunter.scan_file(img_path)
    assert res.has_exif is False
    assert res.filename == "test.jpg"


@pytest.mark.asyncio
async def test_identity_hunter():
    from value_enhancer.modules.identity import IdentityHunter
    hunter = IdentityHunter(timeout=4.0)
    # Test on a known public handle on GitHub
    results = await hunter.scan("torvalds", platforms=["GitHub"])
    assert len(results) == 1
    assert results[0].platform == "GitHub"
    assert results[0].exists is True


def test_orchestrator_summary():
    orchestrator = ReconOrchestrator()
    report = orchestrator.scan_phone("+1 650-253-0000")
    assert report.target_type == TargetType.PHONE
    assert report.risk_score > 0
    assert report.phone_results is not None
