"""
Enterprise Java Static Analyzer Pro
Main Entry Point - Streamlit UI Application

This is the main entry point that coordinates the UI and analysis engine.
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from analyzer_engine import StaticAnalyzerEngine
from scanner import DirectoryScanner, ScanReport
from utils.ui_components import (
    render_executive_summary,
    render_code_metrics,
    render_visualizations,
    render_detailed_findings,
    render_source_code_viewer,
    render_summary_report,
    render_landing_page
)
from utils.helpers import format_file_size


def initialize_session_state():
    """Initialize session state variables for persistent data storage."""
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'analysis_metrics' not in st.session_state:
        st.session_state.analysis_metrics = None
    if 'source_code' not in st.session_state:
        st.session_state.source_code = None
    if 'file_name' not in st.session_state:
        st.session_state.file_name = None
    if 'scan_report' not in st.session_state:
        st.session_state.scan_report = None


def render_scan_summary(report: ScanReport):
    """
    Render the dedup summary column for a directory scan report.

    Shows raw hit count, unique file count after normalization,
    and the number of duplicate file entries collapsed by dedup.
    """
    st.markdown("###   Scan Deduplication Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Raw Hits", report.raw_hit_count)
    with col2:
        st.metric("Unique Files (deduped)", report.unique_file_count)
    with col3:
        st.metric("Collapsed Duplicates", report.collapsed_count)

    rows = [
        {"File": entry.display_path, "Hits": len(entry.hits)}
        for entry in report.files
    ]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)


def export_scan_report_html(report: ScanReport, output_path: str) -> str:
    """
    Export a scan report as a self-contained HTML page that can be
    opened directly in any browser.

    Args:
        report: Aggregated ScanReport
        output_path: Destination file path for the HTML

    Returns:
        The output path written
    """
    rows = "\n".join(
        f"<tr><td>{entry.display_path}</td><td>{len(entry.hits)}</td></tr>"
        for entry in report.files
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Scan Report - {report.root}</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.8rem; text-align: left; }}
.metric {{ display: inline-block; margin-right: 2rem; }}
.metric .value {{ font-size: 2rem; font-weight: 700; }}
</style>
</head>
<body>
<h1>Scan Deduplication Summary</h1>
<p>Scan root: <code>{report.root}</code></p>
<div class="metric"><div class="value">{report.raw_hit_count}</div>Raw Hits</div>
<div class="metric"><div class="value">{report.unique_file_count}</div>Unique Files (deduped)</div>
<div class="metric"><div class="value">{report.collapsed_count}</div>Collapsed Duplicates</div>
<h2>Files</h2>
<table>
<tr><th>File</th><th>Hits</th></tr>
{rows}
</table>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(html)
    return output_path


def configure_page():
    """Configure Streamlit page settings and custom CSS."""

    
    # Custom CSS styling
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(120deg, #1e3a8a 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            color: #64748b;
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the main application header."""
    st.markdown('<h1 class="main-header">  Java Static Analyzer</h1>', 
                unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Advanced Technical Debt Detection & Code Quality Intelligence Platform</p>', 
                unsafe_allow_html=True)


def render_sidebar():
    """
    Render the sidebar with file upload and configuration options.
    
    Returns:
        Tuple of (uploaded_file, analyze_button_clicked, config_dict)
    """
    with st.sidebar:
        st.markdown("###  Control Center")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload Java Source File",
            type=["java"],
            help="Select a .java file for comprehensive analysis"
        )
        
        st.markdown("---")
        
        # Analysis configuration
        with st.expander(" Analysis Configuration"):
            enable_design = st.checkbox("Design Smells", value=True)
            enable_implementation = st.checkbox("Implementation Smells", value=True)
            enable_naming = st.checkbox("Naming Conventions", value=True)
            enable_documentation = st.checkbox("Documentation", value=True)
        
        config = {
            'design': enable_design,
            'implementation': enable_implementation,
            'naming': enable_naming,
            'documentation': enable_documentation
        }
        
        # Analyze button
        analyze_btn = st.button(
            " [START]  Run Deep Analysis",
            type="primary",
            use_container_width=True
        )

        st.markdown("---")

        # Directory scan with path dedup
        with st.expander("  Directory Scan"):
            scan_dir = st.text_input("Scan root directory", value="")
            scan_btn = st.button("Run Directory Scan", use_container_width=True)
            if scan_btn and scan_dir:
                report = DirectoryScanner(scan_dir).scan()
                st.session_state.scan_report = report
            if st.session_state.scan_report is not None:
                html_path = st.text_input("HTML export path", value="scan_report.html")
                if st.button("Export HTML Report", use_container_width=True):
                    export_scan_report_html(st.session_state.scan_report, html_path)
                    st.success(f"Report written to {html_path}")
        
        st.markdown("---")
        
        # Analysis scope information
        st.markdown("###  Analysis Scope")
        st.markdown("""
        - ✅ Design Pattern Violations
        - ✅ Cyclomatic Complexity
        - ✅ Code Smell Detection
        - ✅ Naming Conventions
        - ✅ Documentation Coverage
        - ✅ Maintainability Index
        """)
        
        st.markdown("---")
        
        # Version and timestamp
        st.caption(" Ahmad Hassan")
        st.caption(" Muhammad Abdullah")
        st.caption(" Nayyar Abbas")
        st.caption(" Faraz Ashraf")
        st.caption(" Ahsan Ali Khan")
        st.caption(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return uploaded_file, analyze_btn, config


def render_file_info(file_name: str, file_size: int, line_count: int):
    """
    Render file information metrics.
    
    Args:
        file_name: Name of the uploaded file
        file_size: Size of the file in bytes
        line_count: Number of lines in the file
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f" **File:** {file_name}")
    with col2:
        st.info(f" **Size:** {file_size} bytes")
    with col3:
        st.info(f" **Lines:** {line_count}")


def handle_analysis(source_code: str, config: dict = None):
    """
    Handle the analysis execution and error handling.
    
    Args:
        source_code: Java source code to analyze
        config: Analysis configuration dictionary
    """
    engine = StaticAnalyzerEngine(source_code, config)
    
    try:
        with st.spinner(" Parsing AST nodes and executing analyzers..."):
            results, tree = engine.run()
            metrics = engine.calculate_metrics(tree)
            
            # Store results in session state
            st.session_state.analysis_results = results
            st.session_state.analysis_metrics = metrics
            
    except ValueError as ve:
        st.error(f"❌ **Validation Error:** {ve}")
        st.info(" [TIP]  Please ensure your Java file has valid syntax and try again.")
    except Exception as e:
        st.error(f"❌ **System Error:** {e}")
        st.exception(e)


def display_analysis_results():
    """Display all analysis results from session state."""
    if st.session_state.scan_report is not None:
        render_scan_summary(st.session_state.scan_report)
        st.markdown("---")

    if st.session_state.analysis_results is not None:
        results = st.session_state.analysis_results
        metrics = st.session_state.analysis_metrics
        df = pd.DataFrame(results) if results else pd.DataFrame()
        
        # Render all dashboard sections
        render_executive_summary(df, metrics)
        st.markdown("---")
        
        render_code_metrics(metrics)
        st.markdown("---")
        
        render_visualizations(df)
        st.markdown("---")
        
        render_detailed_findings(df)
        
        # Source code viewer
        render_source_code_viewer(st.session_state.source_code)
        
        # Summary report
        render_summary_report(df, metrics, st.session_state.file_name)


def main():
    """Main application entry point."""
    # Initialize
    initialize_session_state()
    configure_page()
    
    # Render header
    render_header()
    
    # Render sidebar and get inputs
    uploaded_file, analyze_btn, config = render_sidebar()
    
    # Main application logic
    if uploaded_file:
        source_code = uploaded_file.getvalue().decode("utf-8")
        
        # Check if this is a new file
        if st.session_state.file_name != uploaded_file.name:
            st.session_state.file_name = uploaded_file.name
            st.session_state.source_code = source_code
            # Reset analysis when new file is uploaded
            st.session_state.analysis_results = None
            st.session_state.analysis_metrics = None
        
        # Display file information
        render_file_info(
            uploaded_file.name,
            len(source_code),
            len(source_code.split('\n'))
        )
        
        # Handle analysis button click
        if analyze_btn:
            handle_analysis(source_code)
        
        # Display results if they exist
        display_analysis_results()
    
    else:
        # Show landing page when no file is uploaded
        render_landing_page()


if __name__ == "__main__":
    import sys

    if "--scan-root" in sys.argv:
        # Direct-open mode: scan a directory, export HTML, open in browser
        import webbrowser

        root = sys.argv[sys.argv.index("--scan-root") + 1]
        output = "scan_report.html"
        if "--html" in sys.argv:
            output = sys.argv[sys.argv.index("--html") + 1]
        scan_report = DirectoryScanner(root).scan()
        export_scan_report_html(scan_report, output)
        webbrowser.open(output)
        print(f"Scan report written to {output}")
    else:
        main()
