import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ConfidenceMeter } from "./ConfidenceMeter";

describe("ConfidenceMeter", () => {
  it("shows 91% for 0.91", () => {
    render(<ConfidenceMeter confidence={0.91} />);
    expect(screen.getByText("91%")).toBeInTheDocument();
  });
});
