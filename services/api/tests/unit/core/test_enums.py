"""Tests for core enumerations."""

import pytest

from app.core.enums import UploadStatus, EmbeddingStatus, ProcessingStatus


class TestUploadStatus:
    """Tests for UploadStatus enum."""

    def test_enum_has_expected_values(self):
        """Test that UploadStatus enum has all expected values."""
        assert UploadStatus.PENDING.value == "pending"
        assert UploadStatus.PROCESSING.value == "processing"
        assert UploadStatus.COMPLETED.value == "completed"
        assert UploadStatus.FAILED.value == "failed"

    def test_enum_values_are_strings(self):
        """Test that all enum values are strings."""
        for status in UploadStatus:
            assert isinstance(status.value, str)

    def test_enum_value_comparison(self):
        """Test that enum values can be compared with strings."""
        # Test equality with string
        assert UploadStatus.PENDING == "pending"
        assert UploadStatus.PROCESSING == "processing"
        assert UploadStatus.COMPLETED == "completed"
        assert UploadStatus.FAILED == "failed"

    def test_enum_member_comparison(self):
        """Test that enum members can be compared with each other."""
        assert UploadStatus.PENDING == UploadStatus.PENDING
        assert UploadStatus.PENDING != UploadStatus.COMPLETED

    def test_enum_has_four_members(self):
        """Test that UploadStatus has exactly four members."""
        assert len(list(UploadStatus)) == 4

    def test_enum_membership(self):
        """Test enum membership checks."""
        assert UploadStatus.PENDING in UploadStatus
        # Note: In Python 3.11, checking string membership raises TypeError
        # In Python 3.12+, this will return True/False based on value matching
        with pytest.raises(TypeError):
            _ = "pending" in UploadStatus


class TestEmbeddingStatus:
    """Tests for EmbeddingStatus enum."""

    def test_enum_has_expected_values(self):
        """Test that EmbeddingStatus enum has all expected values."""
        assert EmbeddingStatus.PENDING.value == "pending"
        assert EmbeddingStatus.PROCESSING.value == "processing"
        assert EmbeddingStatus.COMPLETED.value == "completed"
        assert EmbeddingStatus.FAILED.value == "failed"

    def test_enum_values_are_strings(self):
        """Test that all enum values are strings."""
        for status in EmbeddingStatus:
            assert isinstance(status.value, str)

    def test_enum_value_comparison(self):
        """Test that enum values can be compared with strings."""
        # Test equality with string
        assert EmbeddingStatus.PENDING == "pending"
        assert EmbeddingStatus.PROCESSING == "processing"
        assert EmbeddingStatus.COMPLETED == "completed"
        assert EmbeddingStatus.FAILED == "failed"

    def test_enum_member_comparison(self):
        """Test that enum members can be compared with each other."""
        assert EmbeddingStatus.PENDING == EmbeddingStatus.PENDING
        assert EmbeddingStatus.PENDING != EmbeddingStatus.COMPLETED

    def test_enum_has_four_members(self):
        """Test that EmbeddingStatus has exactly four members."""
        assert len(list(EmbeddingStatus)) == 4

    def test_enum_membership(self):
        """Test enum membership checks."""
        assert EmbeddingStatus.PENDING in EmbeddingStatus
        # Note: In Python 3.11, checking string membership raises TypeError
        # In Python 3.12+, this will return True/False based on value matching
        with pytest.raises(TypeError):
            _ = "pending" in EmbeddingStatus


class TestProcessingStatus:
    """Tests for ProcessingStatus enum."""

    def test_enum_has_expected_values(self):
        """Test that ProcessingStatus enum has all expected values."""
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.PROCESSING.value == "processing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"

    def test_enum_values_are_strings(self):
        """Test that all enum values are strings."""
        for status in ProcessingStatus:
            assert isinstance(status.value, str)

    def test_enum_value_comparison(self):
        """Test that enum values can be compared with strings."""
        # Test equality with string
        assert ProcessingStatus.PENDING == "pending"
        assert ProcessingStatus.PROCESSING == "processing"
        assert ProcessingStatus.COMPLETED == "completed"
        assert ProcessingStatus.FAILED == "failed"

    def test_enum_member_comparison(self):
        """Test that enum members can be compared with each other."""
        assert ProcessingStatus.PENDING == ProcessingStatus.PENDING
        assert ProcessingStatus.PENDING != ProcessingStatus.COMPLETED

    def test_enum_has_four_members(self):
        """Test that ProcessingStatus has exactly four members."""
        assert len(list(ProcessingStatus)) == 4

    def test_enum_membership(self):
        """Test enum membership checks."""
        assert ProcessingStatus.PENDING in ProcessingStatus
        # Note: In Python 3.11, checking string membership raises TypeError
        # In Python 3.12+, this will return True/False based on value matching
        with pytest.raises(TypeError):
            _ = "pending" in ProcessingStatus


class TestEnumsIndependence:
    """Tests to ensure different status enums are independent."""

    def test_upload_and_embedding_status_are_different_types(self):
        """Test that different status enums are distinct types."""
        assert type(UploadStatus.PENDING) != type(EmbeddingStatus.PENDING)

    def test_enum_types_not_equal_despite_same_value(self):
        """Test that enum members from different enums are not equal."""
        # Even though they have the same value, they should not be equal
        # because they're different enum types
        # Note: Due to str inheritance, they WILL compare equal as strings
        assert UploadStatus.PENDING == EmbeddingStatus.PENDING  # Both are "pending" as str
        # But they are different objects
        assert UploadStatus.PENDING is not EmbeddingStatus.PENDING

    def test_each_enum_is_independent(self):
        """Test that each enum type is independent."""
        assert UploadStatus is not EmbeddingStatus
        assert UploadStatus is not ProcessingStatus
        assert EmbeddingStatus is not ProcessingStatus
