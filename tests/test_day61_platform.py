"""Tests for the Day61 unified behavioral pipeline platform adapter."""

import pytest

from app.platform.unified_behavioral_pipeline import (
    UnifiedBehavioralPipelinePlatformAdapter,
)
from app.unified_behavioral_pipeline import (
    UnifiedBehavioralPipeline,
)


def test_adapter_can_be_created():
    adapter = UnifiedBehavioralPipelinePlatformAdapter()

    assert adapter is not None
    assert isinstance(
        adapter.pipeline,
        UnifiedBehavioralPipeline,
    )


def test_custom_pipeline_can_be_injected():
    pipeline = UnifiedBehavioralPipeline()

    adapter = UnifiedBehavioralPipelinePlatformAdapter(
        pipeline=pipeline,
    )

    assert adapter.pipeline is pipeline


def test_pipeline_property_returns_underlying_pipeline():
    adapter = UnifiedBehavioralPipelinePlatformAdapter()

    assert isinstance(
        adapter.pipeline,
        UnifiedBehavioralPipeline,
    )


def test_adapter_does_not_expose_authorization_api():
    adapter = UnifiedBehavioralPipelinePlatformAdapter()

    assert not hasattr(adapter, "authorize")
    assert not hasattr(adapter, "execute")
    assert not hasattr(adapter, "enforce")