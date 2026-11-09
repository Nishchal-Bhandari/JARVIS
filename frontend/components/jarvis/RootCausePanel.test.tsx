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
  it("shows why runner-up causes lost", () => {
    render(<RootCausePanel rootCause={{ service: "postgres-primary", label: "Database connection pool exhaustion", confidence: 0.91, evidence: ["First anomaly in the incident"], alternatives: [{ service: "payment-service", confidence: 0.05, score: 0.42, factors: { earliness: 0.5, upstream: 0.2, signature: 0, severity: 0.66 }, why_not: ["First anomaly 30s after postgres-primary", "No matching failure signature"] }] }} />);
    expect(screen.getByText("Why not the others?")).toBeInTheDocument();
    expect(screen.getByText("payment-service")).toBeInTheDocument();
    expect(screen.getByText("First anomaly 30s after postgres-primary")).toBeInTheDocument();
  });
  it("says uncertain below 0.5", () => {
    render(<RootCausePanel rootCause={{ service: "x", label: "Unknown", confidence: 0.3, evidence: [], alternatives: [] }} />);
    expect(screen.getByText("Root cause uncertain")).toBeInTheDocument();
  });
});
