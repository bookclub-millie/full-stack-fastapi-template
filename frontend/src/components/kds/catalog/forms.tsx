import {
  Attachment,
  AttachmentAction,
  AttachmentActions,
  AttachmentContent,
  AttachmentDescription,
  AttachmentMedia,
  AttachmentTitle,
} from "@kds/ui/components/attachment"
import { Calendar } from "@kds/ui/components/calendar"
import { Checkbox } from "@kds/ui/components/checkbox"
import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "@kds/ui/components/combobox"
import { DirectionProvider } from "@kds/ui/components/direction"
import { Field, FieldDescription, FieldLabel } from "@kds/ui/components/field"
import { Input } from "@kds/ui/components/input"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
  InputGroupText,
} from "@kds/ui/components/input-group"
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSeparator,
  InputOTPSlot,
} from "@kds/ui/components/input-otp"
import { Label } from "@kds/ui/components/label"
import {
  NativeSelect,
  NativeSelectOption,
} from "@kds/ui/components/native-select"
import {
  Questionnaire,
  QuestionnaireActions,
  QuestionnaireChoice,
  QuestionnaireChoices,
  QuestionnaireDescription,
  QuestionnaireItem,
  QuestionnaireNext,
  QuestionnaireProgress,
  QuestionnaireSkip,
  QuestionnaireSubmit,
  QuestionnaireTitle,
} from "@kds/ui/components/questionnaire"
import { RadioGroup, RadioGroupItem } from "@kds/ui/components/radio-group"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@kds/ui/components/select"
import { Switch } from "@kds/ui/components/switch"
import { Textarea } from "@kds/ui/components/textarea"
import { CalendarDays, FileText, X } from "lucide-react"
import type { ReactNode } from "react"
import { Specimen } from "./specimen"

export function FormSpecimens({ slider }: { slider: ReactNode }) {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Specimen
        name="input"
        title="Input"
        description="A labelled text input with placeholder and disabled states."
      >
        <Field>
          <FieldLabel htmlFor="catalog-display-name">표시 이름</FieldLabel>
          <Input
            autoComplete="off"
            id="catalog-display-name"
            placeholder="이름을 입력하세요"
          />
          <FieldDescription>다른 예시에 표시되는 이름입니다.</FieldDescription>
        </Field>
      </Specimen>

      <Specimen
        name="field"
        title="Field"
        description="Field composes a visible label, control, and helper copy."
      >
        <Field>
          <FieldLabel htmlFor="catalog-email">이메일 주소</FieldLabel>
          <Input
            autoComplete="email"
            id="catalog-email"
            placeholder="name@example.com"
            type="email"
          />
          <FieldDescription>
            유효한 이메일 형식으로 입력하세요.
          </FieldDescription>
        </Field>
      </Specimen>

      <Specimen
        name="label"
        title="Label"
        description="The label is explicitly associated with its native control."
      >
        <div className="grid gap-2">
          <Label htmlFor="catalog-label-example">읽기 쉬운 이름</Label>
          <Input id="catalog-label-example" placeholder="입력 필드" />
        </div>
      </Specimen>

      <Specimen
        name="input-group"
        title="Input Group"
        description="A text field with a persistent unit and a clear accessible name."
      >
        <div className="grid gap-2">
          <Label htmlFor="catalog-search">검색어</Label>
          <InputGroup>
            <InputGroupInput id="catalog-search" placeholder="토큰 검색" />
            <InputGroupAddon align="inline-end">
              <InputGroupText>⌘ K</InputGroupText>
            </InputGroupAddon>
          </InputGroup>
        </div>
      </Specimen>

      <Specimen
        name="input-otp"
        title="Input OTP"
        description="A six-character one-time code field with a visible group label."
      >
        <div className="grid gap-2">
          <Label htmlFor="catalog-otp">인증 코드</Label>
          <InputOTP aria-label="6자리 인증 코드" id="catalog-otp" maxLength={6}>
            <InputOTPGroup>
              <InputOTPSlot index={0} />
              <InputOTPSlot index={1} />
              <InputOTPSlot index={2} />
            </InputOTPGroup>
            <InputOTPSeparator />
            <InputOTPGroup>
              <InputOTPSlot index={3} />
              <InputOTPSlot index={4} />
              <InputOTPSlot index={5} />
            </InputOTPGroup>
          </InputOTP>
        </div>
      </Specimen>

      <Specimen
        name="checkbox"
        title="Checkbox"
        description="A labelled binary option with a visible checked state."
      >
        <div className="flex items-start gap-3">
          <Checkbox defaultChecked id="catalog-terms" />
          <div className="grid gap-1">
            <Label htmlFor="catalog-terms">토큰 사용 기준 확인</Label>
            <p className="text-xs leading-5 text-muted-foreground">
              선택 상태를 키보드와 포인터로 변경할 수 있습니다.
            </p>
          </div>
        </div>
      </Specimen>

      <Specimen
        name="radio-group"
        title="Radio Group"
        description="Mutually exclusive choices with explicit labels."
      >
        <RadioGroup
          aria-label="밀도 선택"
          defaultValue="comfortable"
          className="gap-3"
        >
          <div className="flex items-center gap-2">
            <RadioGroupItem id="density-comfortable" value="comfortable" />
            <Label htmlFor="density-comfortable">여유 있게</Label>
          </div>
          <div className="flex items-center gap-2">
            <RadioGroupItem id="density-compact" value="compact" />
            <Label htmlFor="density-compact">조밀하게</Label>
          </div>
        </RadioGroup>
      </Specimen>

      <Specimen
        name="switch"
        title="Switch"
        description="A labelled on/off preference with an initial enabled state."
      >
        <div className="flex items-center justify-between gap-4">
          <div className="grid gap-1">
            <Label htmlFor="catalog-preview-switch">미리보기 활성화</Label>
            <p className="text-xs text-muted-foreground">
              현재 모드의 토큰을 표시합니다.
            </p>
          </div>
          <Switch defaultChecked id="catalog-preview-switch" />
        </div>
      </Specimen>

      {slider}

      <Specimen
        name="textarea"
        title="Textarea"
        description="A labelled multiline control with a short helper message."
      >
        <Field>
          <FieldLabel htmlFor="catalog-description">설명</FieldLabel>
          <Textarea
            id="catalog-description"
            placeholder="컴포넌트 사용 상황을 적어주세요"
            rows={3}
          />
          <FieldDescription>입력은 이 예시에만 유지됩니다.</FieldDescription>
        </Field>
      </Specimen>

      <Specimen
        name="select"
        title="Select"
        description="A custom select exposes its selected value and keyboard menu."
      >
        <div className="grid gap-2">
          <Label htmlFor="catalog-token-select">토큰 역할</Label>
          <Select defaultValue="surface">
            <SelectTrigger
              aria-label="토큰 역할"
              className="w-full"
              id="catalog-token-select"
            >
              <SelectValue placeholder="역할 선택" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="surface">Surface</SelectItem>
              <SelectItem value="text">Text</SelectItem>
              <SelectItem value="border">Border</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </Specimen>

      <Specimen
        name="native-select"
        title="Native Select"
        description="The platform select keeps its native keyboard and high-contrast behavior."
      >
        <div className="grid gap-2">
          <Label htmlFor="catalog-native-select">표시 모드</Label>
          <NativeSelect defaultValue="light" id="catalog-native-select">
            <NativeSelectOption value="light">라이트</NativeSelectOption>
            <NativeSelectOption value="dark">다크</NativeSelectOption>
          </NativeSelect>
        </div>
      </Specimen>

      <Specimen
        name="combobox"
        title="Combobox"
        description="Searchable options support text filtering and keyboard selection."
      >
        <div className="grid gap-2">
          <Label htmlFor="catalog-combobox">토큰 모드 검색</Label>
          <Combobox>
            <ComboboxInput
              aria-label="토큰 모드 검색"
              id="catalog-combobox"
              placeholder="모드 검색"
            />
            <ComboboxContent>
              <ComboboxList>
                <ComboboxItem value="light">라이트 모드</ComboboxItem>
                <ComboboxItem value="dark">다크 모드</ComboboxItem>
                <ComboboxItem value="contrast">고대비 모드</ComboboxItem>
                <ComboboxEmpty>일치하는 모드가 없습니다.</ComboboxEmpty>
              </ComboboxList>
            </ComboboxContent>
          </Combobox>
        </div>
      </Specimen>

      <Specimen
        name="calendar"
        title="Calendar"
        description="Navigate the month and select a date using keyboard or pointer."
      >
        <Calendar
          aria-label="날짜 선택 달력"
          className="mx-auto"
          defaultMonth={new Date(2025, 4, 1)}
          mode="single"
        />
      </Specimen>

      <Specimen
        name="attachment"
        title="Attachment"
        description="File status is explicit and removal remains a labelled button."
      >
        <Attachment state="uploading">
          <AttachmentMedia>
            <FileText aria-hidden="true" />
          </AttachmentMedia>
          <AttachmentContent>
            <AttachmentTitle>kds-token-guide.pdf</AttachmentTitle>
            <AttachmentDescription>업로드 중 · 2.4 MB</AttachmentDescription>
          </AttachmentContent>
          <AttachmentActions>
            <AttachmentAction aria-label="첨부 제거">
              <X aria-hidden="true" />
            </AttachmentAction>
          </AttachmentActions>
        </Attachment>
      </Specimen>

      <Specimen
        name="questionnaire"
        title="Questionnaire"
        description="A generic one-step preference form with keyboard shortcuts and progress."
      >
        <Questionnaire
          aria-label="테마 선호도"
          defaultItem="mode"
          items={[
            {
              name: "mode",
              required: true,
              choices: [{ value: "light" }, { value: "dark" }],
            },
          ]}
        >
          <QuestionnaireProgress className="text-xs text-muted-foreground" />
          <QuestionnaireItem name="mode" required>
            <QuestionnaireTitle>선호하는 토큰 모드</QuestionnaireTitle>
            <QuestionnaireDescription>
              예시 미리보기에 사용할 모드를 선택합니다.
            </QuestionnaireDescription>
            <QuestionnaireChoices className="mt-3 grid gap-2">
              <QuestionnaireChoice value="light" defaultChecked>
                라이트
              </QuestionnaireChoice>
              <QuestionnaireChoice value="dark">다크</QuestionnaireChoice>
            </QuestionnaireChoices>
          </QuestionnaireItem>
          <QuestionnaireActions className="flex flex-wrap gap-2">
            <QuestionnaireSkip>건너뛰기</QuestionnaireSkip>
            <QuestionnaireNext>계속</QuestionnaireNext>
            <QuestionnaireSubmit>완료</QuestionnaireSubmit>
          </QuestionnaireActions>
        </Questionnaire>
      </Specimen>

      <Specimen
        name="direction"
        title="Direction Provider"
        description="Base UI directional behavior can be checked without changing the site language."
      >
        <DirectionProvider direction="rtl">
          <div
            dir="rtl"
            className="flex items-center gap-2 rounded-lg border border-border bg-muted/40 p-3"
          >
            <CalendarDays
              aria-hidden="true"
              className="size-4 text-muted-foreground"
            />
            <span className="text-sm">오른쪽에서 왼쪽 흐름</span>
          </div>
        </DirectionProvider>
      </Specimen>
    </div>
  )
}
