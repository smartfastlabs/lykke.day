import { useNavigate, useParams } from "@solidjs/router";
import { Component, Show, createResource, createSignal } from "solid-js";
import DetailPage from "@/components/shared/DetailPage";
import FactoidForm from "@/components/factoids/Form";
import FactoidPreview from "@/components/factoids/Preview";
import { factoidAPI } from "@/utils/api";
import { Factoid } from "@/types/api";

const FactoidDetailPage: Component = () => {
  const params = useParams();
  const navigate = useNavigate();
  const [error, setError] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);

  const [factoid] = createResource<Factoid | undefined, string>(
    () => params.id,
    async (id) => factoidAPI.get(id)
  );

  const handleUpdate = async (partialFactoid: Partial<Factoid>) => {
    const current = factoid();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await factoidAPI.update({
        ...current,
        ...partialFactoid,
        id: current.id,
      });
      navigate("/me/settings/factoids");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to update factoid";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    const current = factoid();
    if (!current || !current.id) return;

    setError("");
    setIsLoading(true);
    try {
      await factoidAPI.delete(current.id);
      navigate("/me/settings/factoids");
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to delete factoid";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Show
      when={factoid()}
      fallback={<div class="text-center text-gray-500 py-8">Loading...</div>}
    >
      {(current) => (
        <DetailPage
          heading="Factoid"
          bottomLink={{
            label: "Back to Factoids",
            url: "/me/settings/factoids",
          }}
          preview={<FactoidPreview factoid={current()} />}
          edit={
            <div class="flex flex-col items-center justify-center px-6 py-8">
              <div class="w-full max-w-sm space-y-6">
                <FactoidForm
                  initialData={current()}
                  onSubmit={handleUpdate}
                  isLoading={isLoading()}
                  error={error()}
                />
              </div>
            </div>
          }
          onDelete={handleDelete}
        />
      )}
    </Show>
  );
};

export default FactoidDetailPage;
