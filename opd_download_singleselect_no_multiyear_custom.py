import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import copy
import openpolicedata as opd
import io

    
class URLDataReader(io.BufferedReader):
    def __init__(self, selected_rows):
        print(f"__init__() Reset skip download. id = {id(self)}")
        self.selected_rows = selected_rows
        self.b = bytearray(b"Hello, World!")
    
    def update_selected_rows(self, selected_rows):
        print(f"update_selected_rows().  id = {id(self)}")
        self.selected_rows = selected_rows
        
    def ready_fire(self):
        #reference global flag  
        st.session_state['should_download'] = True
        print(f"ready_fire(). id = {id(self)}")
        return True
    
    def read(self, size: int = -1) -> bytes:

        #TODO stop ignoring size
        if not st.session_state['should_download']:
            print(f"read() Skipping download. size = {size}, id = {id(self)}")
            return self.b
        else:
            print(f"read() Downloading. size = {size}, id = {id(self)}")
        
        selected_rows = self.selected_rows
        if selected_rows is None:
            return self.b
        
        print(f'***source_name={selected_rows.iloc[0]["SourceName"]}, state={selected_rows.iloc[0]["State"]}')
        src = opd.Source(source_name=selected_rows.iloc[0]["SourceName"], state=selected_rows.iloc[0]["State"])        
        types = src.get_tables_types()
        print(types)
        years = src.get_years(table_type=types[0])
        print(years)
        print(f'***year={selected_rows.iloc[0]["Year"]}, table_type={selected_rows.iloc[0]["TableType"]}')
        print("Downloading data from URL")
        data_from_url = src.load_from_url(year=int(selected_rows.iloc[0]["Year"]), table_type=selected_rows.iloc[0]["TableType"]) 
        print(f"Data downloaded from URL. Total of {len(data_from_url.table)} rows")
        csv_text = data_from_url.table.to_csv(index=False)
        csv_text_output = csv_text.encode('utf-8', 'surrogateescape')
        print(f"csv_text_output len is {len(csv_text_output)} id = {id(self)}, type(csv_text_output) = {type(csv_text_output)}")
        st.session_state['should_download'] = False
        self.b.extend(csv_text_output)
        return self.b

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        # Do nothing, since seeking is not supported for this reader
        pass

    

#create a global flag to say if should download or not  (default to false)  

if 'should_download' not in st.session_state:    
    print("Reset download flag")
    st.session_state['should_download'] = False
    st.session_state['url_data_reader'] = URLDataReader(None)
    
else:
    print("SKIP reset download flag")
    
    
if 'selected_rows' not in st.session_state:    
    st.session_state['selected_rows'] = None


@st.cache_data
def get_data_catalog():
    df = opd.datasets.query()
    df = df[~df['Year'].isin(['MULTI', 'NONE'])]
    df['Year'] = df['Year'].astype(str)
    return df


data_catalog = get_data_catalog()

st.header('Selected dataset to download')
expander_container = st.container()

# # Define the data as a dictionary
# data = {
#     'Name': ['Alice', 'Bob', 'Charlie', 'David'],
#     'Age': [25, 30, 35, 40],
#     'City': ['New York', 'San Francisco', 'Los Angeles', 'Chicago']
# }

collect_help = "This collects the data from the data source such as a URL and will make it ready for download. This may take some time."

st.session_state['url_data_reader'].update_selected_rows(st.session_state['selected_rows'])
if st.download_button('Download CSV', data=st.session_state['url_data_reader'] , file_name="selected_rows.csv", on_click=st.session_state['url_data_reader'].ready_fire, mime='text/csv'):
    print('Download complete!!!!!')    

show_all_datasets = st.checkbox('Show all datasets available')
if show_all_datasets == True:
    st.dataframe(data=data_catalog)

with st.sidebar:
    selectbox_states = st.selectbox('States', pd.unique(
        data_catalog['State']), help='Select the states you want to download data for')
    if len(selectbox_states) == 0:
        selected_rows = copy.deepcopy(data_catalog)
    else:
        selected_rows = data_catalog[data_catalog['State'].isin([selectbox_states])]

    selectbox_sources = st.selectbox('Available sources', pd.unique(
        pd.unique(selected_rows['SourceName'])), help='Select the sources')

    if len(selectbox_sources) == 0:
        selected_rows = copy.deepcopy(selected_rows)
    else:        
        selected_rows = selected_rows[selected_rows['SourceName'].isin(
            [selectbox_sources])]

    selectbox_table_types = st.selectbox('Available table types', pd.unique(
        pd.unique(selected_rows['TableType'])), help='Select the table type')

    if len(selectbox_table_types) == 0:       
        selected_rows = copy.deepcopy(selected_rows)
    else:
        selected_rows = selected_rows[selected_rows['TableType'].isin(
            [selectbox_table_types])]

    selectbox_years = st.selectbox('Available years', pd.unique(
        pd.unique(selected_rows['Year'])), help='Select the year')

    if len(selectbox_years) == 0:
        selected_rows = copy.deepcopy(selected_rows)
    else:
        selected_rows = selected_rows[selected_rows['Year'].isin([selectbox_years])]
    st.session_state['selected_rows']=selected_rows

with expander_container:
    st.dataframe(data=selected_rows)