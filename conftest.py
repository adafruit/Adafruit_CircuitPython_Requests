# SPDX-FileCopyrightText: 2023 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" PyTest Setup """

import pytest
import adafruit_connectionmanager


@pytest.fixture(autouse=True)
def reset_connection_manager(monkeypatch):
    """Reset the ConnectionManager, since it's a singlton and will hold data"""
    monkeypatch.setattr(
        "adafruit_requests.get_connection_manager",
        adafruit_connectionmanager.ConnectionManager,
    )
