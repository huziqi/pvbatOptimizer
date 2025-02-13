import os

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

def get_test_data_path(filename: str) -> str:
    return os.path.join(TEST_DATA_DIR, filename)