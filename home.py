import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def app():
    st.markdown("""
        <style>
        .card {
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
            transition: 0.3s;
            border-radius: 5px;
            padding: 16px;
            margin: 16px;
        }
        

        .icon-shape {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 3rem;
            height: 3rem;
            margin: 16px;
            border-radius: 0.5rem;
            color: #fff;
        }
        .bg-gradient-primary {
            background: linear-gradient(87deg,#11cdef 0,#1171ef 100%)!important;
        }
        .font-weight-bold {
            font-weight: 700!important;
        }
        .numbers {
            font-size: 1.25rem;
            font-weight: 600;
        }
        .center {
            text-align: center;
        }
        .large-text {
            font-size: 1.5em;
            font-weight: bold;
        }
        .text-sm {
            font-size: 1.5rem !important;  /* Increase the font size here */
        }   
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
                <div class="card card-primary">
                    <div class="numbers">
                        <p class="text-sm mb-0 text-capitalize font-weight-bold">Model's Accuracy</p>
                        <h5 class="font-weight-bolder mb-0">71,43 %</h5>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
        with col2:
            st.markdown("""
                <div class="card card-secondary">
                    <div class="numbers">
                        <p class="text-sm mb-0 text-capitalize font-weight-bold">Used Images</p>
                        <h5 class="font-weight-bolder mb-0">122</h5>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Data for chart
    birads_data = {
        'BIRADS 1': 37,
        'BIRADS 2': 65,
        'BIRADS 3': 7,
        'BIRADS 4': 10,
        'BIRADS 5': 3
    }
    # Chart
    st.markdown('<div class="center large-text">Number of images in each BIRADS Class in our data</div>', unsafe_allow_html=True)
    fig, ax = plt.subplots(figsize=(2, 2))  # Adjust the figsize to make the chart smaller
    ax.pie(birads_data.values(), labels=birads_data.keys(), autopct='%1.1f%%', startangle=140, textprops={'fontsize': 6})
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    st.pyplot(fig)      
