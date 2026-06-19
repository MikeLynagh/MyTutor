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
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Textarea } from "@/components/ui/textarea"
import { useParams } from "next/navigation";


const learningContent = [
    {
        id: "search",
        title: "Search for high quality resources",
    },
    {
        id: "upload",
        title: "I'll add my own material",
    },
    {
        id: "search_and_upload",
        title: "Both",
    },
] as const


const formSchema = z.object({
    learningContent: z.string().min(1, "Choose your learning resources."),
    optionalResources: z.string().max(2000, "Keep this under 2000 characters.").optional(),
});


export default function Page() {
    const params = useParams<{ missionId: string }>();
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            learningContent: 'search',
            optionalResources: '',
        },
    })


    function onSubmit(data: z.infer<typeof formSchema>) {
        try {
            const payload = {
                missionId: params.missionId,
                learningContent: data.learningContent,
                optionalResources: data.optionalResources,
            }

            toast("Learning content noted", {
                description: (
                    <pre className="mt-2 w-[320px] overflow-x-auto rounded-md bg-code p-4 text-code-foreground">
                        <code>{JSON.stringify(payload, null, 2)}</code>
                    </pre>
                ),
                position: "bottom-right",
            })
        }
        catch (error) {
            console.error('saved to fail form data', error)

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
                        How should the tutor create your mission?
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form id="mission-plan-form" onSubmit={form.handleSubmit(onSubmit)}>
                        <FieldGroup>
                            <Controller
                                name="learningContent"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <FieldLabel>How should the tutor create your mission?</FieldLabel>
                                        <RadioGroup
                                            onValueChange={field.onChange}
                                            value={field.value}
                                            className="flex flex-col gap-3"
                                        >
                                            {learningContent.map((preference) => {
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
                                name="optionalResources"
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
                    <Button type="button" variant="outline" onClick={() => form.reset()}>
                        Reset
                    </Button>
                    <Button type="submit" form="mission-plan-form">
                        Generate Mission Plan
                    </Button>
                </CardFooter>
            </Card>
            <Toaster />

        </main>
    )

}
