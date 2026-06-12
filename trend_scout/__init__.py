"""TrendScout — weekly discovery of in-demand supplement ingredients.

Pipeline: discover candidate ingredients (Google Trends rising queries +
Reddit) -> filter to plausible ingredients -> score momentum from Google
Trends -> emit a ranked sheet and breakout alerts with Kalodata search links.
"""

__version__ = "0.1.0"
