import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Timeline } from "./Timeline";

describe("Timeline", () => {
  it("renders stages with offsets", () => {
    render(<Timeline stages={[
      { t: "2026-11-09T10:15:00Z", offset_seconds: 0, services: ["postgres-primary"], key_events: ["pool exhausted"] },
      { t: "2026-11-09T10:15:11Z", offset_seconds: 11, services: ["payment-service"], key_events: ["timeout"] },
    ]} />);
    expect(screen.getByText("+0s")).toBeInTheDocument();
    expect(screen.getByText("+11s")).toBeInTheDocument();
    expect(screen.getByText("payment-service")).toBeInTheDocument();
  });
});
