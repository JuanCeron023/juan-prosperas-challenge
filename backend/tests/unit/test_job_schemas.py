"""Unit tests for job Pydantic schemas."""

from datetime import date

import pytest
from pydantic import ValidationError

from backend.app.jobs.schemas import DateRange, JobCreateRequest


class TestJobCreateRequest:
    """Tests for JobCreateRequest schema."""

    def test_valid_job_create_request(self):
        """A valid request with all required fields is accepted."""
        request = JobCreateRequest(
            report_type="sales",
            date_range=DateRange(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            ),
            format="csv",
        )
        assert request.report_type == "sales"
        assert request.format == "csv"
        assert request.priority == "standard"

    def test_invalid_report_type_rejected(self):
        """An invalid report_type value is rejected with a validation error."""
        with pytest.raises(ValidationError) as exc_info:
            JobCreateRequest(
                report_type="invalid_type",
                date_range=DateRange(
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 1, 31),
                ),
                format="csv",
            )
        errors = exc_info.value.errors()
        assert any("report_type" in str(e.get("loc", "")) for e in errors)

    def test_invalid_format_rejected(self):
        """An invalid format value is rejected with a validation error."""
        with pytest.raises(ValidationError) as exc_info:
            JobCreateRequest(
                report_type="sales",
                date_range=DateRange(
                    start_date=date(2024, 1, 1),
                    end_date=date(2024, 1, 31),
                ),
                format="xlsx",
            )
        errors = exc_info.value.errors()
        assert any("format" in str(e.get("loc", "")) for e in errors)

    def test_priority_defaults_to_standard(self):
        """When priority is not specified, it defaults to 'standard'."""
        request = JobCreateRequest(
            report_type="inventory",
            date_range=DateRange(
                start_date=date(2024, 2, 1),
                end_date=date(2024, 2, 28),
            ),
            format="pdf",
        )
        assert request.priority == "standard"


class TestDateRange:
    """Tests for DateRange schema."""

    def test_date_range_start_after_end_rejected(self):
        """A date range where start_date > end_date is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DateRange(
                start_date=date(2024, 12, 31),
                end_date=date(2024, 1, 1),
            )
        assert "start_date must be before or equal to end_date" in str(exc_info.value)

    def test_date_range_same_day_accepted(self):
        """A date range where start_date == end_date is accepted."""
        dr = DateRange(
            start_date=date(2024, 6, 15),
            end_date=date(2024, 6, 15),
        )
        assert dr.start_date == dr.end_date
