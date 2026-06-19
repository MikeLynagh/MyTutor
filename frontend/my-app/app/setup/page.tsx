"use client";
import * as React from "react"
import { zodResolver } from "@hookform/resolvers/zod";
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { useRouter } from "next/navigation";



const learningLevel = [
    {
        id: "beginner",
        title: "Beginner",
    },
    {
        id: "some_knowledge",
        title: "Some Knowledge",
    },
    {
        id: "comfortable",
        title: "Comfortable",
    },
] as const

const learningStyle = [
    {
        id: "short",
        title: "Short Explanations",
    },
    {
        id: "quiz_often",
        title: "Quiz me often",
    },
    {
        id: "step_by_step",
        title: "Step by Step",
    },
] as const


const formSchema = z.object({
    learnTopic: z
        .string()
        .min(5, "Topic must be at least 5 characters.")
        .max(300, "Topic must be at most 300 characters."),
    motivationTopic: z
        .string()
        .min(5, "Entry must be at least 5 characters.")
        .max(300, "Entry must be at most 300 characters."),
    successDefined: z
        .string()
        .min(5, "You need to define your success")
        .max(300, "Limit is 300 chars"),
    currentLevel: z.string().min(1, "Choose your current level."),
    learningStyle: z.string().min(1, "Choose your learning preference."),
});


export default function Page() {
    const router = useRouter();
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            learnTopic: '',
            motivationTopic: '',
            successDefined: '',
            currentLevel: 'beginner',
            learningStyle: 'short'
        },
    })


    async function onSubmit(data: z.infer<typeof formSchema>) {
        try {
            const payload = {
                goal: data.learnTopic,
                why: data.motivationTopic,
                success_criteria: data.successDefined,
                current_level: data.currentLevel,
                learning_preference: data.learningStyle,
                source_mode: "web",
            }

            const apiUrl = process.env.NEXT_PUBLIC_API_URL

            const response = await fetch(`${apiUrl}/api/missions`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload)
            })

            if(!response.ok){
                throw new Error(`Failed to create mission: ${response.status}`)
            }

            const mission = await response.json()

            const missionId = mission.id;

            toast("Mission created", {
            description: (
                <pre className="mt-2 w-[320px] overflow-x-auto rounded-md bg-code p-4 text-code-foreground">
                    <code>{JSON.stringify(mission, null, 2)}</code>
                </pre>
            ),
            position: "bottom-right",
            router.push(`/missions/${missionId}/plan`)
        })
        console.log("Created mission", mission)
        }
        catch (error){
            console.error('saved to fail form data', error)

            toast("Something went wrong", {
                description: "Could not create your learning mission",
                position: "bottom-right",
            })
        }
    }

    return (
        <main className="flex min-h-screen items-center justify-center bg-background p-6">
            <Card className="w-full max-w-md">
                <CardHeader>
                    <CardTitle>Adaptive AI Tutor</CardTitle>
                    <CardDescription>
                        Learn new skills through active recall and feedback.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form id="form-rhf-demo" onSubmit={form.handleSubmit(onSubmit)}>
                        <FieldGroup>
                            <Controller
                                name="learnTopic"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <FieldLabel htmlFor="form-rhf-demo-title">
                                            What do you want to learn?
                                        </FieldLabel>
                                        <Input
                                            {...field}
                                            id="form-rhf-demo-title"
                                            aria-invalid={fieldState.invalid}
                                            placeholder="e.g FastAPI basics for building an AI backend"
                                            autoComplete="off"
                                        />
                                        {fieldState.invalid && (
                                            <FieldError errors={[fieldState.error]} />
                                        )}
                                    </Field>
                                )}
                            />
                            <Controller
                                name="motivationTopic"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <FieldLabel htmlFor="form-rhf-demo-title">
                                            Why are you learning this?
                                        </FieldLabel>
                                        <Input
                                            {...field}
                                            id="form-rhf-demo-motivation"
                                            aria-invalid={fieldState.invalid}
                                            placeholder="e.g I need this skill for an exam"
                                            autoComplete="off"
                                        />
                                        {fieldState.invalid && (
                                            <FieldError errors={[fieldState.error]} />
                                        )}
                                    </Field>
                                )}
                            />
                            <Controller
                                name="successDefined"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <FieldLabel htmlFor="form-rhf-demo-successDefined">
                                            What would success look like?
                                        </FieldLabel>
                                        <Input
                                            {...field}
                                            id="form-rhf-demo-successDefined"
                                            aria-invalid={fieldState.invalid}
                                            placeholder="e.g I can build a working FastAPI backend myself"
                                            autoComplete="off"
                                        />
                                        {fieldState.invalid && (
                                            <FieldError errors={[fieldState.error]} />
                                        )}
                                    </Field>
                                )}
                            />
                            <Controller
                                name="currentLevel"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <FieldLabel>Current level</FieldLabel>
                                        <RadioGroup
                                            onValueChange={field.onChange}
                                            value={field.value}
                                            className="flex flex-col space-y-1"
                                        >
                                            {learningLevel.map((level) => {
                                                const id = `current-level-${level.id}`

                                                return (
                                                    <div key={level.id} className="flex items-center space-x-2">
                                                        <RadioGroupItem value={level.id} id={id} />
                                                        <Label htmlFor={id}>{level.title}</Label>
                                                    </div>
                                                )
                                            })}
                                        </RadioGroup>
                                        {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                                    </Field>
                                )}
                            />
                            <Controller
                                name="learningStyle"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <FieldLabel>Learning preference</FieldLabel>
                                        <RadioGroup
                                            onValueChange={field.onChange}
                                            value={field.value}
                                            className="flex flex-col space-y-1"
                                        >
                                            {learningStyle.map((level) => {
                                                const id = `learning-style-${level.id}`

                                                return (
                                                    <div key={level.id} className="flex items-center space-x-2">
                                                        <RadioGroupItem value={level.id} id={id} />
                                                        <Label htmlFor={id}>{level.title}</Label>
                                                    </div>
                                                )
                                            })}
                                        </RadioGroup>
                                        {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
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
                    <Button type="submit" form="form-rhf-demo">
                        Submit
                    </Button>
                </CardFooter>
            </Card>
            <Toaster />

        </main>
    )

}
