# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Environment variable loader for the Personal Assistant Demo."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_environment_variables():
    """
    Load environment variables from .env file.
    
    Looks for .env file in the project root directory and loads
    environment variables from it. Falls back to system environment
    variables if .env file is not found.
    """
    # Find the project root (where .env should be located)
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent.parent  # Go up to repo root
    env_file = project_root / ".env"
    
    if env_file.exists():
        logger.info(f"Loading environment variables from {env_file}")
        load_dotenv(env_file)
    else:
        logger.info("No .env file found, using system environment variables")
        logger.info(f"Expected .env file location: {env_file}")
        logger.info("Copy .env.example to .env and fill in your API keys")


def get_required_env_var(var_name: str) -> str:
    """
    Get a required environment variable.
    
    Args:
        var_name: Name of the environment variable
        
    Returns:
        The environment variable value
        
    Raises:
        ValueError: If the environment variable is not set
    """
    value = os.getenv(var_name)
    if not value:
        raise ValueError(
            f"Required environment variable {var_name} is not set. "
            f"Please set it in your .env file or system environment."
        )
    return value


def get_optional_env_var(var_name: str, default: str = "") -> str:
    """
    Get an optional environment variable.
    
    Args:
        var_name: Name of the environment variable
        default: Default value if not set
        
    Returns:
        The environment variable value or default
    """
    return os.getenv(var_name, default)


# Load environment variables when this module is imported
load_environment_variables()
