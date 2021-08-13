import streamlit as st

tab_list = ['Home','Resources','Gallery','Vision','About']

if "tab_index" not in st.session_state:
    st.session_state.tab_index = 0
def next_tab():
    assert(len(tab_list) > 0)
    st.session_state.tab_index = (st.session_state.tab_index + 1) % len(tab_list)

# create a button in the side bar that will move to the next page/radio button choice
st.sidebar.button('Next on list', on_click=next_tab)

# create your radio button with the index that we loaded
choice = st.sidebar.radio("go to",('Home','Resources', 'Gallery', 'Vision', 'About'), index=st.session_state.tab_index)

st.title(choice)
# finally get to whats on each page
if choice == 'Home':
    st.write('this is home')
elif choice == 'Resources':
    st.write('here is a resources page')
elif choice == 'Gallery':
    st.write('A Gallery of some sort')
elif choice == 'Vision':
    st.write('The Vision')
elif choice == 'About':
    st.write('About page')

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 