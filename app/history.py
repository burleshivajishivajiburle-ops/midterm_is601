"""
History management for storing and retrieving calculations.

This module provides comprehensive history management with pandas serialization
to CSV files. It supports saving calculation history, loading from files,
searching, filtering, and maintaining history with size limits.
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import json
import uuid

from .exceptions import HistoryError, FileOperationError, ValidationError

# Type aliases
CalculationDict = Dict[str, Any]
HistoryFilter = Dict[str, Any]


class CalculationHistory:
    """
    Manages calculation history with pandas-based serialization.
    
    Provides functionality to store, retrieve, search, and manage calculation
    history using pandas DataFrames and CSV file persistence. Supports
    filtering, sorting, and size management.
    """
    
    # Standard columns for history DataFrame
    HISTORY_COLUMNS = [
        "id",
        "timestamp", 
        "operation",
        "operand_a",
        "operand_b", 
        "result",
        "expression",
        "success",
        "error_message",
        "duration_ms"
    ]
    
    def __init__(self, 
                 history_file: Optional[str] = None,
                 max_entries: int = 1000,
                 auto_save: bool = True):
        """
        Initialize the calculation history manager.
        
        Args:
            history_file (str, optional): Path to history CSV file
            max_entries (int): Maximum number of history entries to keep
            auto_save (bool): Whether to auto-save after each addition
        """
        self.history_file = history_file
        self.max_entries = max_entries
        self.auto_save = auto_save
        self._history: pd.DataFrame = pd.DataFrame(columns=self.HISTORY_COLUMNS)
        
        # Load existing history if file exists
        if self.history_file and Path(self.history_file).exists():
            self.load_history()
    
    def add_calculation(self, calculation_data: CalculationDict) -> str:
        """
        Add a calculation to the history.
        
        Args:
            calculation_data (CalculationDict): Calculation data to add
            
        Returns:
            str: Unique ID of the added calculation
            
        Raises:
            HistoryError: If addition fails
        """
        try:
            # Generate unique ID if not provided
            calc_id = calculation_data.get("id", str(uuid.uuid4()))
            
            # Prepare row data
            row_data = {
                "id": calc_id,
                "timestamp": calculation_data.get("timestamp", datetime.now().isoformat()),
                "operation": calculation_data.get("operation", ""),
                "operand_a": calculation_data.get("operand_a"),
                "operand_b": calculation_data.get("operand_b"),
                "result": calculation_data.get("result"),
                "expression": calculation_data.get("expression", ""),
                "success": calculation_data.get("error") is None,
                "error_message": calculation_data.get("error", ""),
                "duration_ms": calculation_data.get("duration_ms", 0)
            }
            
            # Add to DataFrame
            new_row = pd.DataFrame([row_data])
            self._history = pd.concat([self._history, new_row], ignore_index=True)
            
            # Apply size limit
            if len(self._history) > self.max_entries:
                self._history = self._history.tail(self.max_entries).reset_index(drop=True)
            
            # Auto-save if enabled
            if self.auto_save and self.history_file:
                self.save_history()
            
            return calc_id
            
        except Exception as e:
            raise HistoryError("add", f"Failed to add calculation: {str(e)}")
    
    def get_calculation(self, calc_id: str) -> Optional[CalculationDict]:
        """
        Get a specific calculation by ID.
        
        Args:
            calc_id (str): Calculation ID to retrieve
            
        Returns:
            Optional[CalculationDict]: Calculation data or None if not found
        """
        try:
            matches = self._history[self._history["id"] == calc_id]
            
            if matches.empty:
                return None
            
            return self._row_to_dict(matches.iloc[0])
            
        except Exception as e:
            raise HistoryError("get", f"Failed to get calculation {calc_id}: {str(e)}")
    
    def get_recent_calculations(self, count: int = 10) -> List[CalculationDict]:
        """
        Get the most recent calculations.
        
        Args:
            count (int): Number of recent calculations to retrieve
            
        Returns:
            List[CalculationDict]: List of recent calculations
        """
        try:
            if self._history.empty:
                return []
            
            # Sort by timestamp (most recent first) and take the requested count
            recent = self._history.sort_values("timestamp", ascending=False).head(count)
            
            return [self._row_to_dict(row) for _, row in recent.iterrows()]
            
        except Exception as e:
            raise HistoryError("get_recent", f"Failed to get recent calculations: {str(e)}")
    
    def search_calculations(self, 
                          operation: Optional[str] = None,
                          result_range: Optional[Tuple[float, float]] = None,
                          date_range: Optional[Tuple[datetime, datetime]] = None,
                          success_only: Optional[bool] = None,
                          limit: Optional[int] = None) -> List[CalculationDict]:
        """
        Search calculations with various filters.
        
        Args:
            operation (str, optional): Filter by operation type
            result_range (Tuple[float, float], optional): Filter by result range (min, max)
            date_range (Tuple[datetime, datetime], optional): Filter by date range
            success_only (bool, optional): Filter by success status
            limit (int, optional): Maximum number of results
            
        Returns:
            List[CalculationDict]: Filtered calculations
        """
        try:
            if self._history.empty:
                return []
            
            df = self._history.copy()
            
            # Apply operation filter
            if operation:
                df = df[df["operation"] == operation]
            
            # Apply result range filter
            if result_range:
                min_val, max_val = result_range
                df = df[
                    (df["result"] >= min_val) & 
                    (df["result"] <= max_val) &
                    (df["result"].notna())
                ]
            
            # Apply date range filter
            if date_range:
                start_date, end_date = date_range
                df["timestamp_dt"] = pd.to_datetime(df["timestamp"])
                df = df[
                    (df["timestamp_dt"] >= start_date) & 
                    (df["timestamp_dt"] <= end_date)
                ]
                df = df.drop("timestamp_dt", axis=1)
            
            # Apply success filter
            if success_only is not None:
                df = df[df["success"] == success_only]
            
            # Sort by timestamp (most recent first)
            df = df.sort_values("timestamp", ascending=False)
            
            # Apply limit
            if limit:
                df = df.head(limit)
            
            return [self._row_to_dict(row) for _, row in df.iterrows()]
            
        except Exception as e:
            raise HistoryError("search", f"Failed to search calculations: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the calculation history.
        
        Returns:
            Dict[str, Any]: Statistics including counts, success rates, etc.
        """
        try:
            if self._history.empty:
                return {
                    "total_calculations": 0,
                    "successful_calculations": 0,
                    "failed_calculations": 0,
                    "success_rate": 0.0,
                    "operations_count": {},
                    "date_range": None,
                    "average_result": None
                }
            
            total = len(self._history)
            successful = len(self._history[self._history["success"] == True])
            failed = total - successful
            success_rate = (successful / total) * 100 if total > 0 else 0.0
            
            # Operation counts
            operations_count = self._history["operation"].value_counts().to_dict()
            
            # Date range
            timestamps = pd.to_datetime(self._history["timestamp"])
            date_range = {
                "earliest": timestamps.min().isoformat() if not timestamps.empty else None,
                "latest": timestamps.max().isoformat() if not timestamps.empty else None
            }
            
            # Average result (for successful calculations with numeric results)
            numeric_results = self._history[
                (self._history["success"] == True) & 
                (self._history["result"].notna()) &
                (pd.to_numeric(self._history["result"], errors='coerce').notna())
            ]["result"]
            
            average_result = float(pd.to_numeric(numeric_results).mean()) if not numeric_results.empty else None
            
            return {
                "total_calculations": total,
                "successful_calculations": successful,
                "failed_calculations": failed,
                "success_rate": round(success_rate, 2),
                "operations_count": operations_count,
                "date_range": date_range,
                "average_result": average_result
            }
            
        except Exception as e:
            raise HistoryError("statistics", f"Failed to get statistics: {str(e)}")
    
    def clear_history(self) -> None:
        """Clear all history entries."""
        try:
            self._history = pd.DataFrame(columns=self.HISTORY_COLUMNS)
            
            if self.auto_save and self.history_file:
                self.save_history()
                
        except Exception as e:
            raise HistoryError("clear", f"Failed to clear history: {str(e)}")
    
    def remove_calculation(self, calc_id: str) -> bool:
        """
        Remove a specific calculation from history.
        
        Args:
            calc_id (str): ID of calculation to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        try:
            initial_len = len(self._history)
            self._history = self._history[self._history["id"] != calc_id].reset_index(drop=True)
            
            removed = len(self._history) < initial_len
            
            if removed and self.auto_save and self.history_file:
                self.save_history()
            
            return removed
            
        except Exception as e:
            raise HistoryError("remove", f"Failed to remove calculation {calc_id}: {str(e)}")
    
    def save_history(self, file_path: Optional[str] = None) -> None:
        """
        Save history to CSV file using pandas.
        
        Args:
            file_path (str, optional): Custom file path, uses default if None
            
        Raises:
            FileOperationError: If save operation fails
        """
        try:
            target_file = file_path or self.history_file
            
            if not target_file:
                raise FileOperationError(
                    "None",
                    "save",
                    "No file path specified for saving history"
                )
            
            # Ensure directory exists
            Path(target_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Save DataFrame to CSV
            self._history.to_csv(target_file, index=False, encoding='utf-8')
            
        except Exception as e:
            raise FileOperationError(
                target_file or "unknown",
                "save",
                f"Failed to save history: {str(e)}"
            )
    
    def load_history(self, file_path: Optional[str] = None) -> None:
        """
        Load history from CSV file using pandas.
        
        Args:
            file_path (str, optional): Custom file path, uses default if None
            
        Raises:
            FileOperationError: If load operation fails
        """
        try:
            source_file = file_path or self.history_file
            
            if not source_file or not Path(source_file).exists():
                raise FileOperationError(
                    source_file or "None",
                    "load",
                    "History file does not exist"
                )
            
            # Load DataFrame from CSV
            loaded_df = pd.read_csv(source_file, encoding='utf-8')
            
            # Validate columns
            missing_columns = set(self.HISTORY_COLUMNS) - set(loaded_df.columns)
            if missing_columns:
                # Add missing columns with default values
                for col in missing_columns:
                    loaded_df[col] = None
            
            # Reorder columns to match expected order
            self._history = loaded_df[self.HISTORY_COLUMNS].copy()
            
            # Apply size limit
            if len(self._history) > self.max_entries:
                self._history = self._history.tail(self.max_entries).reset_index(drop=True)
            
        except pd.errors.EmptyDataError:
            # File is empty, start with empty DataFrame
            self._history = pd.DataFrame(columns=self.HISTORY_COLUMNS)
        except Exception as e:
            raise FileOperationError(
                source_file or "unknown",
                "load",
                f"Failed to load history: {str(e)}"
            )
    
    def export_history(self, 
                      file_path: str,
                      format: str = "csv",
                      filters: Optional[HistoryFilter] = None) -> None:
        """
        Export history to various formats.
        
        Args:
            file_path (str): Path for exported file
            format (str): Export format ("csv", "json", "excel")
            filters (HistoryFilter, optional): Filters to apply before export
            
        Raises:
            FileOperationError: If export fails
        """
        try:
            # Apply filters if provided
            df = self._history.copy()
            if filters:
                if "operation" in filters:
                    df = df[df["operation"] == filters["operation"]]
                if "success_only" in filters:
                    df = df[df["success"] == filters["success_only"]]
                # Add more filters as needed
            
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Export based on format
            if format.lower() == "csv":
                df.to_csv(file_path, index=False, encoding='utf-8')
            elif format.lower() == "json":
                df.to_json(file_path, orient='records', indent=2, date_format='iso')
            elif format.lower() == "excel":
                df.to_excel(file_path, index=False, engine='openpyxl')
            else:
                raise ValidationError(format, "Unsupported export format", "Use 'csv', 'json', or 'excel'")
            
        except Exception as e:
            raise FileOperationError(
                file_path,
                "export",
                f"Failed to export history: {str(e)}"
            )
    
    def _row_to_dict(self, row: pd.Series) -> CalculationDict:
        """
        Convert a pandas Series row to a calculation dictionary.
        
        Args:
            row (pd.Series): DataFrame row
            
        Returns:
            CalculationDict: Calculation data dictionary
        """
        return {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "operation": row["operation"],
            "operand_a": row["operand_a"],
            "operand_b": row["operand_b"],
            "result": row["result"],
            "expression": row["expression"],
            "success": row["success"],
            "error": row["error_message"] if row["error_message"] else None,
            "duration_ms": row["duration_ms"]
        }
    
    def get_count(self) -> int:
        """Get the total number of calculations in history."""
        return len(self._history)
    
    def is_empty(self) -> bool:
        """Check if history is empty."""
        return self._history.empty
    
    def get_last_calculation(self) -> Optional[CalculationDict]:
        """
        Get the most recent calculation.
        
        Returns:
            Optional[CalculationDict]: Most recent calculation or None if empty
        """
        if self._history.empty:
            return None
        
        latest = self._history.sort_values("timestamp", ascending=False).iloc[0]
        return self._row_to_dict(latest)
    
    def get_operation_history(self, operation: str, limit: int = 10) -> List[CalculationDict]:
        """
        Get history for a specific operation.
        
        Args:
            operation (str): Operation type to filter by
            limit (int): Maximum number of results
            
        Returns:
            List[CalculationDict]: Calculations for the specified operation
        """
        return self.search_calculations(operation=operation, limit=limit)
    
    def __len__(self) -> int:
        """Return the number of calculations in history."""
        return len(self._history)
    
    def __str__(self) -> str:
        """String representation of the history."""
        return f"CalculationHistory(entries={len(self._history)}, file={self.history_file})"
    
    def __repr__(self) -> str:
        """Developer representation of the history."""
        return (f"CalculationHistory(entries={len(self._history)}, "
                f"max_entries={self.max_entries}, "
                f"auto_save={self.auto_save}, "
                f"file='{self.history_file}')")