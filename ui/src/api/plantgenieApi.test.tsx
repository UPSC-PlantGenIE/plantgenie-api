import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { plantgenieApi } from "./plantgenieApi";
import { server } from "../mocks/server";
import { renderWithStore } from "../test-utils";

describe("plantgenieApi", () => {
  it("sends the stored account id as a bearer token", async () => {
    let authorization: string | null = null;
    server.use(
      http.get("http://localhost:8000/api/v2/lists", ({ request }) => {
        authorization = request.headers.get("authorization");
        return HttpResponse.json({ lists: [] });
      })
    );

    const { store } = renderWithStore(<div />, {
      preloadedState: { account: { accountId: "1234567890123456" } },
    });

    await store.dispatch(
      plantgenieApi.endpoints.getMyLists.initiate(undefined)
    );

    expect(authorization).toBe("Bearer 1234567890123456");
  });
});
