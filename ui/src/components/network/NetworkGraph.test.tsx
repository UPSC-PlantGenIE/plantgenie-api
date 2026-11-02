import { describe, it, expect, vi, beforeEach } from "vitest";
import { openNetworkGraph } from "../../networkGraph/feature";
import { renderWithStore } from "../../test-utils";
import NetworkGraph from "./NetworkGraph";

vi.mock("../../networkGraph/feature", () => ({
  openNetworkGraph: vi.fn(() => ({ destroy: vi.fn() })),
}));

const opened = () => vi.mocked(openNetworkGraph).mock.calls[0][0];

const props = {
  listId: "abc",
  listName: "Drought genes",
  annotationId: "arath-Araport11",
  taxonName: "Arabidopsis thaliana",
};

describe("NetworkGraph", () => {
  beforeEach(() => vi.mocked(openNetworkGraph).mockClear());

  it("opens the feature once for the list", () => {
    renderWithStore(<NetworkGraph {...props} onClose={() => {}} />);

    expect(openNetworkGraph).toHaveBeenCalledTimes(1);
    expect(opened().listId).toBe("abc");
    expect(opened().listName).toBe("Drought genes");
    expect(opened().annotationId).toBe("arath-Araport11");
    expect(opened().taxonName).toBe("Arabidopsis thaliana");
    expect(opened().apiRoot).toMatch(/\/v2$/);
  });

  it("sends the account as a bearer token, and nothing when logged out", () => {
    renderWithStore(<NetworkGraph {...props} onClose={() => {}} />, {
      preloadedState: { account: { accountId: "1234" } },
    });
    expect(opened().getHeaders?.()).toEqual({ Authorization: "Bearer 1234" });
  });

  it("sends no header without an account", () => {
    renderWithStore(<NetworkGraph {...props} onClose={() => {}} />, {
      preloadedState: { account: { accountId: null } },
    });
    expect(opened().getHeaders?.()).toEqual({});
  });

  it("calls onClose when the feature closes", () => {
    const onClose = vi.fn();
    renderWithStore(<NetworkGraph {...props} onClose={onClose} />);

    opened().onClose?.();

    expect(onClose).toHaveBeenCalled();
  });

  it("destroys the feature on unmount", () => {
    const destroy = vi.fn();
    vi.mocked(openNetworkGraph).mockReturnValueOnce({ destroy });
    const { unmount } = renderWithStore(
      <NetworkGraph {...props} onClose={() => {}} />
    );

    unmount();

    expect(destroy).toHaveBeenCalled();
  });
});
