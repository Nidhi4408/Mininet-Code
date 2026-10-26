#!/usr/bin/env python3

import os
import sys
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=== Generating Performance Comparison with Base Paper ===")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ensure directories exist
    os.makedirs('comparison', exist_ok=True)
    
    try:
        from monitoring.comparison_analyzer import ComparisonMonitor
        comparison_monitor = ComparisonMonitor()
        
        # Generate comparison graphs
        print("Generating comparison graphs...")
        comparison_monitor.generate_all_comparison_graphs()
        
        # Generate comparison table
        print("Generating comparison table...")
        comparison_df = comparison_monitor.generate_comparison_table()
        
        print("✓ All comparison graphs and tables generated successfully!")
        print("\n" + "="*70)
        print("PERFORMANCE COMPARISON SUMMARY")
        print("="*70)
        print(comparison_df.to_string(index=False))
        print("\n📊 Comparison graphs saved in 'comparison/' directory")
        
    except Exception as e:
        print(f"✗ Error generating comparison: {e}")

if __name__ == '__main__':
    main()