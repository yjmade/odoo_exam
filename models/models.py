# -*- coding: utf-8 -*-
import random
import datetime
from openerp import models, fields, api, _, exceptions


class ExamStatus(models.Model):
    _name = "examin.exam.status"
    _order = "sequence"

    name = fields.Char(size=20, translate=True)
    sequence = fields.Integer()


class Exam(models.Model):
    _name = 'examin.exam'
    _rec_name = "name"

    name = fields.Text()
    question_num = fields.Integer(string="Question Count")
    category = fields.Many2one("examin.question.category")
    user_lines = fields.One2many("examin.user.participant", "exam")
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    exam_minutes = fields.Integer()
    users = fields.Many2many("res.users", compute="_get_users", inverse="_set_users")

    def get_default_status(self):
        return self.env["examin.exam.status"].search([("name", "=", "Draft")])

    status = fields.Many2one("examin.exam.status", default=get_default_status)

    @api.one
    @api.depends("user_lines")
    def _get_users(self):
        self.users = self.env["res.users"].browse([user_line.user.id for user_line in self.user_lines])

    def _set_users(self):
        exist_user_lines = {
            user_line.user: user_line
            for user_line in self.user_lines
        }
        for user in self.users:
            if user not in exist_user_lines:
                self._generate_user_line(user)

    def _generate_user_line(self, user):
        user_line_model = self.env["examin.user.participant"]
        question_line_model = self.env["examin.user.participant.line"]
        user_line = user_line_model.create({
            "user": user.id,
            "exam": self.id,
            "status": "pending",
            "score": False
        })
        ids = list(self.category.questions.ids)
        random.shuffle(ids)
        for i, question_id in enumerate(ids[:self.question_num], 1):
            question_line_model.create({
                "user_examin": user_line.id,
                "question": question_id,
                "seq": i
            })

    @api.onchange("category")
    def onchange_category(self):
        if self.category:
            self.name = _("%s Test") % self.category.name
            self.question_num = self.category.question_count
        else:
            self.name = False
            self.question_num = 0

    @api.onchange("start_time")
    def onchange_start_time(self):

        if self.start_time:
            self.end_time = fields.Datetime.to_string(fields.Datetime.from_string(self.start_time) + datetime.timedelta(hours=2))
        else:
            self.end_time = False


class Question(models.Model):
    _name = "examin.question"
    _rec_name = "body"

    category = fields.Many2one("examin.question.category")
    body = fields.Text()
    choice_a = fields.Text()
    choice_b = fields.Text()
    choice_c = fields.Text()
    choice_d = fields.Text()
    answer = fields.Selection([
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ])

    @property
    def choices(self):
        return [(choice, getattr(self, "choice_%s" % choice)) for choice in ["a", "b", "c", "d"]]


class Category(models.Model):
    _name = "examin.question.category"
    _rec_name = "name"

    name = fields.Text()
    questions = fields.One2many("examin.question", "category")
    exams = fields.One2many("examin.exam", "category")
    question_count = fields.Integer(compute="_get_question_count")

    @api.multi
    @api.depends("questions")
    def _get_question_count(self):
        counts = {group["category"][0]: group["category_count"] for group in self.env["examin.question"].read_group([["category.id", "in", self.ids]], [], ["category"])}
        for rec in self:
            rec.question_count = counts.get(rec.id, 0)

    @api.multi
    def action_questions(self, *args, **kwargs):
        return {
            'name': self.name,
            'view_mode': 'tree,form',
            # 'view_type': 'tree',
            'res_model': 'examin.question',
            # 'res_id': partial_id,
            'type': 'ir.actions.act_window',
            # 'nodestroy': True,
            # 'target': 'new',
            'domain': [("category.id", "=", self.id)],
            "context": {'default_category': self.id}
        }


class UserExamin(models.Model):
    _name = "examin.user.participant"
    _rec_name = "exam"
    user = fields.Many2one("res.users")
    exam = fields.Many2one("examin.exam")
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    total_minutes = fields.Integer(compute="_get_total_minutes")
    lines = fields.One2many("examin.user.participant.line", "user_examin")
    score = fields.Float()
    status = fields.Selection([
        ("pending", "pending"),
        ("examing", "examing"),
        ('finish', "finish")
    ])

    @api.one
    @api.depends("start_time", "end_time")
    def _get_total_minutes(self):
        from_string = fields.Datetime.from_string
        if self.start_time and self.end_time:
            self.total_minutes = (from_string(self.end_time) - from_string(self.start_time)).total_seconds() // 60
        else:
            self.total_minutes = False

    @api.multi
    def action_start_test(self):
        self.ensure_one()
        if not self.status == "pending":
            raise exceptions.ValidationError(_("Exam has been taken"))
        if self.search([("user.id", "=", self.user.id), ("status", "=", "examing")]):
            raise exceptions.ValidationError(_("Cannot have more than one exam taking at once"))
        self.sudo().write(dict(
            status="examing",
            start_time=fields.Datetime.now()
        ))
        url = "/examin/do_exam/%s/" % self.id
        return {
            "type": 'ir.actions.act_url',
            "url": url,
            "target": "self"
        }

    @api.multi
    def action_resume_test(self):
        self.ensure_one()
        if not self.status == "examing":
            raise exceptions.ValidationError(_("Exam has not start yet"))
        url = "/examin/do_exam/%s/" % self.id
        return {
            "type": 'ir.actions.act_url',
            "url": url,
            "target": "self"
        }

    @api.one
    def caculate_score(self):

        result = [question_line.correct for question_line in self.lines]
        data = dict(
            score=result.count(True) * 1. / len(result) * 100,
            status="finish",
            end_time=fields.Datetime.now()
        )
        self.write(data)


class UserExaminLine(models.Model):
    _name = "examin.user.participant.line"
    _rec_name = "question"
    _order = "seq"
    user_examin = fields.Many2one("examin.user.participant", string="Exam")
    seq = fields.Integer()
    question = fields.Many2one("examin.question")
    answer = fields.Selection([
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ], string="Choice")
    answer_time = fields.Datetime()
    display_answer = fields.Text(string=_("Answer"), compute="_get_display_answer")
    correct = fields.Boolean(compute="_get_correct", store=True)

    @api.one
    @api.depends("question", "answer")
    def _get_correct(self):
        self.correct = (self.answer == self.question.answer)

    @api.one
    @api.depends("question", "answer")
    def _get_display_answer(self):
        if self.answer:
            self.display_answer = getattr(self.question, "choice_%s" % self.answer.lower())
        else:
            self.display_answer = False


class ResUser(models.Model):
    _inherit = 'res.users'

    ref_id = fields.Char(string=_("Ref Id"))
    exams = fields.One2many("examin.user.participant", "user")

    def _sync_value(self, value):
        if "name" in value:
            value.setdefault("login", value["name"])
        if "ref_id" in value:
            value.setdefault("password", value["ref_id"])
        return value

    @api.multi
    def write(self, value):
        return super(ResUser, self).write(self._sync_value(value))

    @api.model
    def create(self, value):
        return super(ResUser, self).create(self._sync_value(value))


class IrModelData(models.Model):
    _inherit = 'ir.model.data'

    def _update(self, cr, uid, model, module, values, xml_id=False, store=True, noupdate=False, mode='init', res_id=False, context=None):
        if model == "res.users":
            if xml_id is False:
                xml_id = ""
        return super(IrModelData, self)._update(cr, uid, model, module, values, xml_id, store, noupdate, mode, res_id, context)
