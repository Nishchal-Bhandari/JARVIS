import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RootCausePanel } from "./RootCausePanel";

describe("RootCausePanel", () => {
  it("shows service, label and evidence", () => {
    render(<RootCausePanel rootCause={{ service: "postgres-primary", label: "Database connection pool exhaustion", confidence: 0.91, evidence: ["First anomaly in the incident"], alternatives: [] }} />);
    expect(screen.getByText("postgres-primary")).toBeInTheDocument();
    expect(screen.getByText("First anomaly in the incident")).toBeInTheDocument();
    expect(screen.getByText("91%")).toBeInTheDocument();
  });
  it("says uncertain below 0.5", () => {
    render(<RootCausePanel rootCause={{ service: "x", label: "Unknown", confidence: 0.3, evidence: [], alternatives: [] }} />);
    expect(screen.getByText("Root cause uncertain")).toBeInTheDocument();
  });
});
