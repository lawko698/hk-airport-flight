import pandas as pd

from flows.utils.helper_function import (get_extracted_status_time,
                                         get_full_load_dates, is_plane_delayed)


def test_is_plane_delayed():
    input_df = pd.DataFrame({'status_timestamp_difference': [-1, 1, -1], 
                             'status': ['Arrived', 'Arrived', 'Cancelled']})
    input_df['is_plane_delayed'] = input_df.apply(lambda x: is_plane_delayed(x), axis=1)

    expected_df = pd.DataFrame({'status_timestamp_difference': [-1, 1, -1], 
                                'status': ['Arrived', 'Arrived', 'Cancelled'], 
                                'is_plane_delayed': [False, True, None]})
    pd.testing.assert_frame_equal(input_df, expected_df)

def test_get_extracted_status_time():
    input_df = pd.DataFrame({'date': ["N/A", "12-06-2024", "12-06-2024", "12-06-2024"],
                             'next_datetime': ["N/A", "12-06-2024 12:00", "12-06-2024 12:00", "N/A"], 
                             'status': ['Cancelled', 'At gate', 'At gate', 'At gate'], 
                             'extract_status_time': ["12:00", "", "12:00", "13:00"]})
    input_df['extract_status_datetime'] = input_df.apply(lambda x: get_extracted_status_time(x), axis=1)

    expected_df = pd.DataFrame({'date': ["N/A", "12-06-2024", "12-06-2024", "12-06-2024"],
                                'next_datetime': ["N/A", "12-06-2024 12:00", "12-06-2024 12:00", "N/A"], 
                                'status': ['Cancelled', 'At gate', 'At gate', 'At gate'], 
                                'extract_status_time': ["12:00", "", "12:00", "13:00"],
                                'extract_status_datetime': [None, None, "12-06-2024 12:00", "12-06-2024 13:00"]})
    
    pd.testing.assert_frame_equal(input_df, expected_df)

def test_get_full_load_dates():
    assert len(get_full_load_dates.fn())  == 89
