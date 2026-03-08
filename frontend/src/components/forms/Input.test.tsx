import { describe, it, expect } from "vitest";
import { render, waitFor } from "@solidjs/testing-library";
import { createSignal, onMount } from "solid-js";

import { Select } from "./Input";

describe("Select", () => {
  it("keeps selected value when options load asynchronously", async () => {
    const AsyncSelect = () => {
      const [value, setValue] = createSignal("custom-slug");
      const [options, setOptions] = createSignal<
        { value: string; label: string }[]
      >([]);

      onMount(() => {
        setOptions([
          { value: "default", label: "Default" },
          { value: "custom-slug", label: "Custom Slug" },
        ]);
      });

      return (
        <Select<string>
          id="async-select"
          value={value}
          onChange={setValue}
          options={options()}
          placeholder="Select an option"
        />
      );
    };

    const { container } = render(() => <AsyncSelect />);

    await waitFor(() => {
      const select = container.querySelector("#async-select") as any;
      expect(select).toBeTruthy();
      expect(select?.value).toBe("custom-slug");
    });
  });
});
