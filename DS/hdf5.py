import h5py
import numpy as np

# Create a new HDF5 file
with h5py.File('example.hdf5', 'w') as f:
    # Create a dataset and write data to it
    dset = f.create_dataset('mydata', data=np.random.randn(1000))
    
    # Add some attributes to the dataset
    dset.attrs['description'] = 'Random numbers'
    dset.attrs['date_created'] = '2025-03-06'

# Read from the HDF5 file
with h5py.File('example.hdf5', 'r') as f:
    # Read the entire dataset
    data = f['mydata'][()]
    
    # Print the first 5 elements
    print("First 5 elements:", data[:5])
    
    # Print attributes
    print("Description:", f['mydata'].attrs['description'])
    print("Date created:", f['mydata'].attrs['date_created'])

    # Calculate and print some statistics
    print("Min value:", np.min(data))
    print("Max value:", np.max(data))
    print("Mean value:", np.mean(data))
