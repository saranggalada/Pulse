### IMPORTING LIBRARIES

import streamlit as st
import numpy as np
import pandas as pd
import random
import time
import pickle


##########################################################################################################

## APP BASIC UI

st.set_page_config(page_icon="img/pulse.png", page_title="Pulse⚡", layout="centered")

st.write("""
         # ⚡Pulse
            Blazing fast 🚀 **PIN Code - Merchant** retrieval engine for ONDC! [`Learn More`](https://docs.google.com/presentation/d/11vU81WRVayVceGUhq59F0aTHsiWjH3yR3yEglaLAFsQ), [`Demo`](https://youtu.be/0y6aefeDs_0)
         """)
st.write('---')


## Sidebar
st.sidebar.image("img/pulse.png")
st.sidebar.markdown("<h2 style='text-align: center;'>⚡Pulse</h2>", unsafe_allow_html=True)
st.sidebar.write('---')
st.sidebar.markdown("""
                    For the [**Build for Bharat 2024**](https://hack2skill.com/build-for-bharat-hackathon-ondc-google-cloud) Hackathon organized by [ONDC](https://ondc.in/) and [Google Cloud](https://cloud.google.com/)')
                    """)
st.sidebar.write('---')
cols = st.sidebar.columns(3)
cols[0].link_button('GitHub', 'https://github.com/saranggalada/Pulse')
cols[1].link_button('Author', 'https://www.linkedin.com/in/saranggalada')
cols[2].link_button('PPT', 'https://docs.google.com/presentation/d/11vU81WRVayVceGUhq59F0aTHsiWjH3yR3yEglaLAFsQ')
st.sidebar.markdown("---\n*Copyright (c) 2024: Sarang Galada*")

st.sidebar.write('---')
st.sidebar.header('See Also')
st.sidebar.markdown(
    """
- [EPL Viz](https://epl-viz.streamlit.app/) 🕵🏼 \
(Visualizing 24 years of EPL!)
- [The Pitch Prophecy](https://pitch-prophecy.streamlit.app/) 🔮 \
(EPL Win Predictor!)
- [The xG Philosophy](https://xg-philosophy.streamlit.app/) 🧙🏼‍♂️ \
(EPL xG Projector!)
"""
)
st.sidebar.markdown('---')


##########################################################################################################

### DATA ARCHITECTURE DESIGN

# Defining the Radix Tree Class - The minimalist data structure used for the Pincode-Merchant Mapping
# A Radix Tree is a space-optimized prefix-based 'trie' data structure used to store a set of strings.
# It offers constant time complexity for search, insert and delete operations.

class RadixTreeNode:
    # Initialize the node with an empty dictionary of children and an empty set of merchant_ids
    def __init__(self):
        self.children = {}
        self.merchant_ids = set()

class RadixTree:
    # Initialize the tree with an empty root node
    def __init__(self):
        self.root = RadixTreeNode()

    # Insert a pincode and its merchant_id into the tree
    def insert(self, pincode, merchant_id):
        pincode = str(pincode)
        node = self.root
        for digit in pincode:
            if digit not in node.children:
                node.children[digit] = RadixTreeNode()
            node = node.children[digit]
        node.merchant_ids.add(merchant_id)

    # Delete a pincode and its merchant_id from the tree
    def delete(self, pincode, merchant_id):
        pincode = str(pincode)
        node = self.root
        for digit in pincode:
            if digit not in node.children:
                return 0 # ie. Pincode not found
            node = node.children[digit]
        node.merchant_ids.discard(merchant_id)

    # Update a pincode and its merchant_id in the tree
    def update(self, old_pincode, new_pincode, merchant_id):
        self.delete(old_pincode, merchant_id)
        self.insert(new_pincode, merchant_id)

    # Check if a pincode exists in the tree
    def exists(self, pincode):
        node = self.root
        for digit in pincode:
            if digit not in node.children:
                return False
            node = node.children[digit]
        return bool(node.merchant_ids)

    # Search for a pincode in the tree and return the merchant_ids
    def search(self, pincode):
        node = self.root
        for digit in pincode:
            if digit not in node.children:
                return set()  # ie. Pincode not found
            node = node.children[digit]
        return node.merchant_ids
    
    # Load a merchant's pincodes into the tree
    def load_merchant(self, merchant_pin_array, merchant_id):
      for pincode in merchant_pin_array:
        self.insert(pincode, merchant_id)

    # Print the tree
    def print_tree(self):
            self._print_node(self.root, "")

    def _print_node(self, node, prefix):
        if node.merchant_ids:
            print(prefix + " -> " + str(node.merchant_ids))
        for digit, child in node.children.items():
            self._print_node(child, prefix + digit)


##########################################################################################################
            
### DATA PREPARATION & STORAGE

## Load an array containing all 19300 existing Indian pincodes (as of Jan 2024)
def get_all_pincodes():
    ## Loading an array containing all 19300 existing Indian pincodes (as of Jan 2024)
    pincodes = pd.read_csv("data/unique indian pincodes.csv", header=None)
    pincodes = pincodes.values.reshape(-1)
    return pincodes

## Generate 'num_merchants' many merchants and randomly assign 'min' to 'max' many real serviceable pincodes to each
def generate_merchant_pincode(num_merchants, min, max, pincodes):
    for i in range(num_merchants):
        # Randomly assign to each merchant a bunch of 'min' to 'max' many unsorted pincodes from the pool
        st = random.randint(0, len(pincodes)-max) # start index
        serviceable_size = random.randint(min, max) # chunk size
        serviceable_pins = pincodes[st:st+serviceable_size] # grab a chunk and assign to merchant

        # save serviceable_pins as an np array
        np.save("data/merchant/merchant"+str(i)+".npy", serviceable_pins)

## Build a Radix Tree with 'num_merchants' many merchants
def build_radix_tree(num_merchants):
    tree = RadixTree()
    t0 = time.time()
    for i in range(num_merchants):
        merchant_pins = np.load("data/merchant/merchant"+str(i)+".npy")
        merchant_id = i
        tree.load_merchant(merchant_pins, merchant_id)
    t1 = time.time()
    return tree, t1-t0      # Additionally returns the time taken to build the tree

## Save the Radix Tree to a file
def save_radix_tree(tree, filename='data/radix_tree.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump(tree, f)

## Load the Radix Tree from a file
@st.cache_resource      # Caching the function to avoid repeated calls
def load_radix_tree(filename='data/radix_tree.pkl'):
    try:
        t0 = time.time()
        with open(filename, 'rb') as f:
            tree = pickle.load(f)
        t1 = time.time()
        return tree, t1-t0      # Additionally returns the time taken to load the tree
    except:
        return RadixTree(), 0

## Upload a Radix Tree file
@st.cache_resource      # Caching the function to avoid repeated calls
def upload_radix_tree(pkl):
    return pickle.load(pkl)

## CSV to Radix Tree
@st.cache_resource      # Caching the function to avoid repeated calls
def csv_to_radix_tree(csv):
    df = pd.read_csv(csv)
    tree = RadixTree()
    for i in df.columns:
        tree.load_merchant(df[i].values, i)
    return tree


##########################################################################################################
        
### MERCHANT APP SIDE
        
## Add a new merchant to the Radix Tree
def add_merchant(tree, merchant_pins, merchant_id):
    tree.load_merchant(merchant_pins, merchant_id)

## Update a merchant's pincodes in the Radix Tree
def update_merchant(tree, old_merchant_pins, new_merchant_pins, merchant_id):
    for pincode in old_merchant_pins:
        tree.delete(pincode, merchant_id)
    tree.load_merchant(new_merchant_pins, merchant_id)

## Remove a merchant from the Radix Tree
def remove_merchant(tree, merchant_id):
    merchant_id = int(merchant_id)
    for pincode in get_all_pincodes():
        merchant_ids = tree.search(str(pincode))
        if merchant_id in merchant_ids:
            tree.delete(pincode, merchant_id)

## Add a new pincode for a merchant to the Radix Tree
def add_pincode(tree, pincode, merchant_id):
    tree.insert(pincode, merchant_id)

## Update a pincode for a merchant in the Radix Tree
def update_pincode(tree, old_pincode, new_pincode, merchant_id):
    tree.update(old_pincode, new_pincode, merchant_id)
    
## Remove a pincode for a merchant from the Radix Tree
def remove_pincode(tree, pincode, merchant_id):
    return tree.delete(pincode, int(merchant_id))


##########################################################################################################

### BUYER APP SIDE
    
## Check if a given pincode is serviceable
def is_serviceable(tree, pincode):
    return tree.exists(pincode)
    
## Search for merchants for a given pincode
def get_merchants(tree, pincode):
    if is_serviceable(tree, pincode):
        pincode = str(pincode)
        t0 = time.time()
        merchant_ids = tree.search(pincode)
        t1 = time.time()
        # st.write(t1-t0)
        return merchant_ids, t1-t0      # Additionally returns the time taken to search the tree
    else:
        return set(), 0

## Save the merchant_ids for a given pincode to a file
def save_merchants(merchant_ids, pincode):
    filename = "data/pincodes/"+str(pincode)+".npy"
    np.save(filename, np.array(list(merchant_ids)))

## Load the merchant_ids for a given pincode from a file
def load_merchants(pincode):
    filename = "data/pincodes/"+str(pincode)+".npy"
    try:
        merchant_ids = np.load(filename)
        return merchant_ids
    except:
        return set()


##########################################################################################################
    
### INITIALIZATION
    
# Load the Radix Tree

if 'registry' not in st.session_state:
    tree, load_time = load_radix_tree()
    st.session_state.registry = tree
else:
    tree = st.session_state.registry

##########################################################################################################

### APP UI

cols = st.columns(2)
admin = cols[0].toggle('Admin 🔑')
user='None'
if(admin):
  cols[0].write('Mode: **Admin 🛠️**')
else:
    cols[0].write('Mode: **User 👨🏻‍💻**')
    user = cols[1].radio('User Mode 👤', ('Customer', 'Merchant'), horizontal=True)
st.write('---')


## Admin Mode
if admin:
    # st.write('##### Upload Existing Registry')
    st.write('Either an existing registry (ie. Radix Tree in `PKL` format) containing all the Merchant - PIN Code mappings can be uploaded **OR** a `CSV file` with Merchant IDs as column names and serviceable PIN codes as column values must be uploaded...from which a Radix Tree-based registry will be built.  [`Sample Data`](https://drive.google.com/drive/folders/11WeynH-EPI471MQIrg1kXN16zF6stdyG)')
    cols = st.columns(2)
    pkl = cols[0].file_uploader('##### 📤 Upload Existing Registry', type=['pkl'])
    csv = cols[1].file_uploader('##### 🔨 Build Registry from CSV', type=['csv'])
    if pkl:
        tree = upload_radix_tree(pkl)
        st.session_state.registry = tree
        cols[0].success('✅ Registry Loaded!')
    if csv:
        tree = csv_to_radix_tree(csv)
        st.session_state.registry = tree
        cols[1].success('✅ Registry Built!')
    st.write('---')

    st.write('##### 🔧 Modify Registry')
    st.write('Add or remove merchants from the registry. New merchant files must be in .npy format and contain the list of PIN codes serviceable by that Merchant. Make sure to specify the Merchant ID first.')
    cols = st.columns(2)
    merchant_id = cols[0].text_input('🧑🏻‍💼Merchant ID', value='1234')
    merchant_pins = cols[1].file_uploader('###### ➕ Add Merchant', type=['npy'])
    rem = cols[0].button('🗑️ **Remove Merchant**')
    if merchant_pins:
        add_merchant(tree, np.load(merchant_pins), merchant_id)
        st.session_state.registry = tree
        cols[0].success('Added Merchant '+merchant_id+'!')
    if rem:
        remove_merchant(tree, merchant_id)
        st.session_state.registry = tree
        cols[1].success('Removed Merchant '+merchant_id+'!')

    # save_radix_tree(tree)
    st.write('---')

    st.write('Add or remove PIN codes for a specific merchant from the registry.')
    cols = st.columns(2)
    merchant_id = cols[0].text_input('👨🏻‍💼 Merchant ID', value='1234')
    pincode = cols[1].text_input('📍 PIN Code', value='110001')
    a = cols[0].button("📌 **Add PIN Code**")
    # u = cols[0].button("🔄 **Update Pincode**")
    r = cols[1].button("❌ **Remove PIN Code**")
    if a:
        add_pincode(tree, pincode, merchant_id)
        st.session_state.registry = tree
        cols[0].success('✅ Saved!')
    if r:
        status = remove_pincode(tree, pincode, merchant_id)
        if status == 0:
            cols[1].error('❌ PIN Not Found!')
        else:
            st.session_state.registry = tree
            cols[1].success('✅ Saved!')

    st.write('---')

    # # Download the Radix Tree
    # st.write('##### 📥 Download Registry')
    # cols = st.columns(2)
    # filename = cols[0].text_input('📦 File Name', value='radix_tree.pkl')
    # d = cols[1].button("📥 **Download**")
    # if d:
    #     save_radix_tree(tree, filename)
    #     cols[1].success('✅ Saved!')

## Merchant Mode
elif user == 'Merchant' and admin == False:
    st.write('##### ⚙️ Merchant Controls')
    st.write('Add or remove PIN codes for your serviceable area.')
    cols = st.columns(2)
    merchant_id = cols[0].text_input('👨‍💼 Merchant ID', value='1234')
    pincode = cols[1].text_input('📍 PIN Code', value='110001')
    a = cols[0].button("📌 **Add PIN Code**")
    # u = cols[0].button("🔄 **Update Pincode**")
    r = cols[1].button("❌ **Remove PIN Code**")
    if a:
        add_pincode(tree, pincode, merchant_id)
        st.session_state.registry = tree
        cols[0].success('✅ Saved!')
    if r:
        status = remove_pincode(tree, pincode, merchant_id)
        if status == 0:
            cols[1].error('❌ PIN Not Found!')
        else:
            st.session_state.registry = tree
            cols[1].success('✅ Saved!')

    # save_radix_tree(tree)
    st.write('---')

## Customer Mode
elif user == 'Customer' and admin == False:
    tree = st.session_state.registry
    cols = st.columns(2)
    pincode = cols[1].text_input('📍 Enter PIN  Code', value='110001')
    c = cols[0].button("❓ **Check Serviceability**")
    s = cols[0].button("🔍 **Search Merchants**")
    # cols[1].write("Actions")
    if c:
        if is_serviceable(tree, pincode):
            st.success('✅ Serviceable!')
        else:
            cols[0].error('❌ Not Serviceable!')
    if s:
        merchant_ids, search_time = get_merchants(tree, pincode)
        # ISSUE: The below line is printing 0 since Streamlit app is unable to sense minute time intervals
        # cols[0].success('Found '+str(len(merchant_ids))+' merchants in '+str(1000000*search_time)+' microseconds!')
        st.success('Found '+str(len(merchant_ids))+' merchants!')
        st.dataframe(pd.DataFrame(merchant_ids, columns=['Merchant IDs']).T)

    st.write('---')
