"use client";
import * as React from "react"
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { Controller, useForm } from "react-hook-form"
import { Toaster, toast } from "sonner"
import * as z from "zod"
import { Button } from "@/components/ui/button"
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle
} from '@/components/ui/card'
import {
    Field,
    FieldDescription,
    FieldError,
    FieldGroup,
    FieldLabel,
} from "@/components/ui/field"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Textarea } from "@/components/ui/textarea"
import { useParams, useRouter } from "next/navigation";
import type {
    Mission,
    MissionPlanRequest,
    SourceMode,
} from "@/types/mission";
import { missionPlanResponseSchema, missionSchema } from "@/types/mission";


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
] as const


const formSchema = z.object({
    sourceMode: z.enum(["web", "user_material", "both"], {
        message: "Choose your learning resources"
    }),
    userMaterial: z.string().max(2000, "Keep this under 2000 characters.").optional(),
});


export default function Page() {
    const params = useParams<{ missionId: string }>();
    const router = useRouter();
    const [mission, setMission] = React.useState<Mission | null>(null);
    const [isLoadingMission, setIsLoadingMission] = React.useState(true);
    const [isGeneratingPlan, setIsGeneratingPlan] = React.useState(false);
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            sourceMode: 'web',
            userMaterial: '',
        },
    })

    React.useEffect(() => {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

        async function loadMission() {
            try {
                const response = await fetch(
                    `${apiUrl.replace(/\/$/, "")}/api/missions/${params.missionId}`
                )

                if (!response.ok) {
                    throw new Error(`Failed to load mission: ${response.status}`)
                }

                const missionResponse = missionSchema.parse(await response.json())
                setMission(missionResponse)
            } catch (error) {
                console.error("failed to load mission", error)
                toast("Could not load mission", {
                    description: "Reload from the mission setup screen and try again.",
                    position: "bottom-right",
                })
            } finally {
                setIsLoadingMission(false)
            }
        }

        void loadMission()
    }, [params.missionId])


    async function onSubmit(data: z.infer<typeof formSchema>) {
        setIsGeneratingPlan(true)
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
            if (!mission) {
                throw new Error("Mission is not loaded")
            }

            const payload: MissionPlanRequest = {
                goal: mission.goal,
                source_mode: data.sourceMode as SourceMode,
                user_material: data.userMaterial || undefined,
            }

            const response = await fetch(
                `${apiUrl.replace(/\/$/, "")}/api/missions/${params.missionId}/plan`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                }
            )

            if (!response.ok) {
                throw new Error(`Failed to generate mission plan: ${response.status}`)
            }

            const plan = missionPlanResponseSchema.parse(await response.json())
            window.sessionStorage.setItem(`mission:${params.missionId}:plan`, JSON.stringify(plan))

            toast("Mission plan generated", {
                description: "Opening the mission workspace.",
                position: "bottom-right",
            })
            router.push(`/missions/${params.missionId}/plan`)
        }
        catch (error) {
            console.error('saved to fail form data', error)
            setIsGeneratingPlan(false)

            toast("Something went wrong", {
                description: "Could not save your preferences",
                position: "bottom-right",
            })
        }
    }

    return (
        <main className="flex min-h-screen items-center justify-center bg-background p-6">
            <Card className="w-full max-w-lg">
                <CardHeader>
                    <CardTitle>Build your learning path</CardTitle>
                    <CardDescription>
                        Choose the context the tutor should use to build your mission.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {isGeneratingPlan ? (
                        <div className="mb-5 rounded-lg border border-indigo-200 bg-indigo-50/70 px-4 py-3">
                            <div className="flex items-start gap-3">
                                <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-indigo-600" />
                                <div>
                                    <p className="text-sm font-medium text-indigo-950">Generating your mission plan</p>
                                    <p className="mt-1 text-sm leading-relaxed text-indigo-900/80">
                                        The tutor is reviewing your goal, checking resources, and building the first objective sequence.
                                    </p>
                                </div>
                            </div>
                        </div>
                    ) : null}
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
                                            disabled={isGeneratingPlan}
                                        >
                                            {sourceMode.map((preference) => {
                                                const id = `learning-content-${preference.id}`

                                                return (
                                                    <div key={preference.id} className="flex items-center gap-2">
                                                        <RadioGroupItem value={preference.id} id={id} />
                                                        <Label htmlFor={id}>{preference.title}</Label>
                                                    </div>
                                                )
                                            })}
                                        </RadioGroup>
                                        {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
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
                                            disabled={isGeneratingPlan}
                                        />
                                        <FieldDescription>
                                            Paste notes, links, videos, documentation, or anything useful.
                                        </FieldDescription>
                                        {fieldState.invalid && (
                                            <FieldError errors={[fieldState.error]} />
                                        )}
                                    </Field>
                                )}
                            />


                        </FieldGroup>
                    </form>
                </CardContent>
                <CardFooter className="justify-end gap-2">
                    <Button type="button" variant="outline" onClick={() => form.reset()} disabled={isGeneratingPlan}>
                        Reset
                    </Button>
                    <Button type="submit" form="mission-plan-form" disabled={isLoadingMission || isGeneratingPlan}>
                        {isGeneratingPlan ? (
                            <>
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Generating plan
                            </>
                        ) : (
                            "Generate Mission Plan"
                        )}
                    </Button>
                </CardFooter>
            </Card>
            <Toaster />

        </main>
    )

}
