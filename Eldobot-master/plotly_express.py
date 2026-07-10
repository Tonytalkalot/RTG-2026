# Wrapper for plotly.express to maintain compatibility
# This allows "import plotly_express as px" to work
from plotly import express as px
import sys
sys.modules['plotly_express'] = px