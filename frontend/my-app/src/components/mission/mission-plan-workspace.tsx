"use client";

import * as React from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { Toaster, toast } from "sonner";
import * as z from "zod";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Textarea } from "@/components/ui/textarea";
import type {
  Mission,
  MissionPlanRequest,
  MissionPlanResponse,
  SourceMode,
} from "@/types/mission";

const sourceMode = [
  {
    id: "web" as SourceMode,
    title: "Search for high quality resources",
  },
  {
    id: "user_material" as SourceMode,
    title: "I'll add my own material",
  },
  {
    id: "both" as SourceMode,
    title: "Both",
  },
] as const;

const formSchema = z.object({
  sourceMode: z.enum(["web", "user_material", "both"], {
    message: "Choose your learning resources",
  }),
  userMaterial: z.string().max(2000, "Keep this under 2000 characters.").optional(),
});

type MissionPlanWorkspaceProps = {
  missionId: string;
};

export default function MissionPlanWorkspace({ missionId }: MissionPlanWorkspaceProps) {
  const [mission, setMission] = React.useState<Mission | null>(null);
  const [isLoadingMission, setIsLoadingMission] = React.useState(true);
  const [plan, setPlan] = React.useState<MissionPlanResponse | null>(null);
  const [planError, setPlanError] = React.useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      sourceMode: "web",
      userMaterial: "",
    },
  });

  React.useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

    async function loadMission() {
      try {
        const storedPlan = window.sessionStorage.getItem(`mission:${missionId}:plan`);
        if (storedPlan) {
          setPlan(JSON.parse(storedPlan) as MissionPlanResponse);
        }

        const storedMission = window.sessionStorage.getItem(`mission:${missionId}`);
        if (storedMission) {
          setMission(JSON.parse(storedMission) as Mission);
        }

        const response = await fetch(`${apiUrl.replace(/\/$/, "")}/api/missions/${missionId}`);

        if (!response.ok) {
          throw new Error(`Failed to load mission: ${response.status}`);
        }

        const missionResponse: Mission = await response.json();
        setMission(missionResponse);
        window.sessionStorage.setItem(`mission:${missionId}`, JSON.stringify(missionResponse));
      } catch (error) {
        console.error("failed to load mission", error);
        toast("Could not load mission", {
          description: "Reload from the mission setup screen and try again.",
          position: "bottom-right",
        });
      } finally {
        setIsLoadingMission(false);
      }
    }

    void loadMission();
  }, [missionId]);

  async function onSubmit(data: z.infer<typeof formSchema>) {
    try {
      setIsSubmitting(true);
      setPlanError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

      if (!mission) {
        throw new Error("Mission is not loaded");
      }

      const payload: MissionPlanRequest = {
        goal: mission.goal,
        source_mode: data.sourceMode as SourceMode,
        user_material: data.userMaterial || undefined,
      };

      const response = await fetch(
        `${apiUrl.replace(/\/$/, "")}/api/missions/${missionId}/plan`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to generate mission plan: ${response.status}`);
      }

      const nextPlan: MissionPlanResponse = await response.json();
      setPlan(nextPlan);
      window.sessionStorage.setItem(`mission:${missionId}:plan`, JSON.stringify(nextPlan));

      toast("Mission plan generated", {
        description: "Your mission workspace has been updated.",
        position: "bottom-right",
      });
    } catch (error) {
      console.error("saved to fail form data", error);
      setPlanError("Could not generate the mission plan. Please review your inputs and try again.");

      toast("Something went wrong", {
        description: "Could not generate your mission plan",
        position: "bottom-right",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <div className="flex flex-col gap-6">
        <Card className="w-full">
          <CardHeader>
            <CardTitle>Build your learning path</CardTitle>
            <CardDescription>How should the tutor create your mission?</CardDescription>
          </CardHeader>
          <CardContent>
            <form id="mission-plan-form" onSubmit={form.handleSubmit(onSubmit)}>
              <FieldGroup>
                <Controller
                  name="sourceMode"
                  control={form.control}
                  render={({ field, fieldState }) => (
                    <Field data-invalid={fieldState.invalid}>
                      <FieldLabel>How should the tutor create your mission?</FieldLabel>
                      <RadioGroup
                        onValueChange={field.onChange}
                        value={field.value}
                        className="flex flex-col gap-3"
                      >
                        {sourceMode.map((preference) => {
                          const id = `learning-content-${preference.id}`;

                          return (
                            <div key={preference.id} className="flex items-center gap-2">
                              <RadioGroupItem value={preference.id} id={id} />
                              <Label htmlFor={id}>{preference.title}</Label>
                            </div>
                          );
                        })}
                      </RadioGroup>
                      {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
                    </Field>
                  )}
                />
                <Controller
                  name="userMaterial"
                  control={form.control}
                  render={({ field, fieldState }) => (
                    <Field data-invalid={fieldState.invalid}>
                      <FieldLabel htmlFor="mission-optional-resources">Optional:</FieldLabel>
                      <Textarea
                        {...field}
                        id="mission-optional-resources"
                        aria-invalid={fieldState.invalid}
                        placeholder=""
                        autoComplete="off"
                        className="min-h-32 resize-none"
                      />
                      <FieldDescription>
                        Paste notes, links, videos, documentation, or anything useful.
                      </FieldDescription>
                      {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
                    </Field>
                  )}
                />
              </FieldGroup>
            </form>
          </CardContent>
          <CardFooter className="justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => form.reset()}>
              Reset
            </Button>
            <Button type="submit" form="mission-plan-form" disabled={isLoadingMission || isSubmitting}>
              {isSubmitting ? "Generating..." : "Generate Mission Plan"}
            </Button>
          </CardFooter>
        </Card>

        {planError ? (
          <Card className="border-destructive/40">
            <CardHeader>
              <CardTitle>Plan Error</CardTitle>
              <CardDescription>{planError}</CardDescription>
            </CardHeader>
          </Card>
        ) : null}

        {plan ? (
          <Card>
            <CardHeader>
              <CardTitle>{mission?.title ?? "Mission plan"}</CardTitle>
              <CardDescription>{plan.source_summary}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <section className="space-y-2">
                <h2 className="text-sm font-semibold uppercase tracking-normal text-muted-foreground">
                  Recommended approach
                </h2>
                <p className="text-sm">{plan.recommended_learning_approach}</p>
              </section>

              <section className="space-y-3">
                <h2 className="text-sm font-semibold uppercase tracking-normal text-muted-foreground">
                  Objectives
                </h2>
                <div className="space-y-3">
                  {plan.objectives.map((objective, index) => (
                    <div key={objective.id} className="rounded-md border p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="text-xs text-muted-foreground">Step {index + 1}</p>
                          <h3 className="text-sm font-semibold">{objective.title}</h3>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Difficulty {objective.difficulty.toFixed(2)}
                        </p>
                      </div>
                      <p className="mt-2 text-sm text-muted-foreground">{objective.description}</p>
                      <div className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                        <div>
                          <p className="font-medium">Assessment</p>
                          <p className="text-muted-foreground">{objective.assessment_type}</p>
                        </div>
                        <div>
                          <p className="font-medium">Prerequisites</p>
                          <p className="text-muted-foreground">
                            {objective.prerequisites.length > 0
                              ? objective.prerequisites.join(", ")
                              : "None"}
                          </p>
                        </div>
                      </div>
                      <div className="mt-3 text-sm">
                        <p className="font-medium">Success criteria</p>
                        <p className="text-muted-foreground">{objective.success_criteria}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </CardContent>
          </Card>
        ) : null}
      </div>
      <Toaster />
    </>
  );
}
