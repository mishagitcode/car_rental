from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any, Dict, List

from flask import Flask, flash, redirect, render_template, request, url_for

from .db import get_db
from .pricing import calculate_cost, days_between, loyalty_factor, parse_date


def available_cars(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
        FROM cars
        WHERE id NOT IN (
            SELECT car_id
            FROM rentals
            WHERE actual_return_date IS NULL
        )
        ORDER BY id DESC
        """
    ).fetchall()


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index() -> str:
        with get_db() as conn:
            totals = conn.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM cars) AS cars,
                    (SELECT COUNT(*) FROM customers) AS customers,
                    (SELECT COUNT(*) FROM rentals) AS rentals
                """
            ).fetchone()
            rentals = conn.execute(
                """
                SELECT r.*, c.make, c.year, c.rental_cost, c.type,
                       cu.last_name, cu.first_name, cu.middle_name
                FROM rentals r
                JOIN cars c ON c.id = r.car_id
                JOIN customers cu ON cu.id = r.customer_id
                ORDER BY r.id DESC
                LIMIT 5
                """
            ).fetchall()
            returned_rentals = conn.execute(
                """
                SELECT r.*, c.make, c.year, c.rental_cost, c.type
                FROM rentals r
                JOIN cars c ON c.id = r.car_id
                WHERE r.actual_return_date IS NOT NULL
                ORDER BY r.actual_return_date DESC
                LIMIT 5
                """
            ).fetchall()
            revenue = 0.0
            for rental in returned_rentals:
                issue = parse_date(rental["date_issue"])
                end_date = parse_date(rental["actual_return_date"])
                days = days_between(issue, end_date)
                loyalty = loyalty_factor(conn, rental["customer_id"])
                cost = calculate_cost(
                    rental,
                    days,
                    loyalty,
                    rental["return_condition"],
                )
                revenue += cost.total
        return render_template(
            "index.html",
            totals=totals,
            recent_rentals=rentals,
            revenue=revenue,
        )

    @app.route("/cars", methods=["GET", "POST"])
    def cars() -> str:
        if request.method == "POST":
            make = request.form.get("make", "").strip()
            year = request.form.get("year", "").strip()
            cost = request.form.get("cost", "").strip()
            rental_cost = request.form.get("rental_cost", "").strip()
            car_type = request.form.get("type", "").strip()
            if not (make and year and cost and rental_cost and car_type):
                flash("All car fields are required.")
            else:
                with get_db() as conn:
                    conn.execute(
                        """
                        INSERT INTO cars (make, year, cost, rental_cost, type)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (make, int(year), float(cost), float(rental_cost), car_type),
                    )
                flash("Car added.")
            return redirect(url_for("cars"))
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM cars ORDER BY id DESC").fetchall()
        return render_template("cars.html", cars=rows)

    @app.route("/customers", methods=["GET", "POST"])
    def customers() -> str:
        if request.method == "POST":
            last_name = request.form.get("last_name", "").strip()
            first_name = request.form.get("first_name", "").strip()
            middle_name = request.form.get("middle_name", "").strip()
            address = request.form.get("address", "").strip()
            phone = request.form.get("phone", "").strip()
            if not (last_name and first_name and address and phone):
                flash("Last name, first name, address, and phone are required.")
            else:
                with get_db() as conn:
                    conn.execute(
                        """
                        INSERT INTO customers
                            (last_name, first_name, middle_name, address, phone)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (last_name, first_name, middle_name, address, phone),
                    )
                flash("Customer added.")
            return redirect(url_for("customers"))
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM customers ORDER BY id DESC"
            ).fetchall()
        return render_template("customers.html", customers=rows)

    @app.route("/rentals", methods=["GET", "POST"])
    def rentals() -> str:
        if request.method == "POST":
            car_id = request.form.get("car_id", "").strip()
            customer_id = request.form.get("customer_id", "").strip()
            date_issue = request.form.get("date_issue", "").strip()
            expected_return_date = request.form.get("expected_return_date", "").strip()
            if not (car_id and customer_id and date_issue and expected_return_date):
                flash("All rental fields are required.")
                return redirect(url_for("rentals"))
            with get_db() as conn:
                car_available = conn.execute(
                    """
                    SELECT 1
                    FROM cars c
                    WHERE c.id = ?
                      AND c.id NOT IN (
                          SELECT car_id FROM rentals WHERE actual_return_date IS NULL
                      )
                    """,
                    (car_id,),
                ).fetchone()
                if not car_available:
                    flash("Selected car is not available.")
                    return redirect(url_for("rentals"))
                conn.execute(
                    """
                    INSERT INTO rentals
                        (car_id, customer_id, date_issue, expected_return_date)
                    VALUES (?, ?, ?, ?)
                    """,
                    (int(car_id), int(customer_id), date_issue, expected_return_date),
                )
            flash("Rental created.")
            return redirect(url_for("rentals"))

        with get_db() as conn:
            car_rows = available_cars(conn)
            customer_rows = conn.execute(
                "SELECT * FROM customers ORDER BY id DESC"
            ).fetchall()
            rows = conn.execute(
                """
                SELECT r.*, c.make, c.year, c.rental_cost, c.type,
                       cu.last_name, cu.first_name, cu.middle_name
                FROM rentals r
                JOIN cars c ON c.id = r.car_id
                JOIN customers cu ON cu.id = r.customer_id
                ORDER BY r.id DESC
                """
            ).fetchall()

            view_rows: List[Dict[str, Any]] = []
            for row in rows:
                issue = parse_date(row["date_issue"])
                end_str = row["actual_return_date"] or row["expected_return_date"]
                end_date = parse_date(end_str)
                days = days_between(issue, end_date)
                loyalty = loyalty_factor(conn, row["customer_id"])
                cost = calculate_cost(row, days, loyalty, row["return_condition"])
                view = dict(row)
                view["days"] = days
                view["end_date"] = end_str
                view["cost"] = cost
                view_rows.append(view)

        return render_template(
            "rentals.html",
            rentals=view_rows,
            cars=car_rows,
            customers=customer_rows,
            today=date.today().isoformat(),
        )

    @app.route("/rentals/<int:rental_id>/return", methods=["POST"])
    def return_rental(rental_id: int) -> str:
        actual_return_date = request.form.get("actual_return_date", "").strip()
        return_condition = request.form.get("return_condition", "good").strip()
        if not actual_return_date:
            flash("Return date is required.")
            return redirect(url_for("rentals"))
        with get_db() as conn:
            conn.execute(
                """
                UPDATE rentals
                SET actual_return_date = ?, return_condition = ?
                WHERE id = ?
                """,
                (actual_return_date, return_condition, rental_id),
            )
        flash("Rental returned.")
        return redirect(url_for("rentals"))
